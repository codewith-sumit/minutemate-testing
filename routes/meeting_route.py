import os
import uuid
import json
import re
from datetime import datetime
from io import BytesIO

from flask import Blueprint, request, session, jsonify, flash, redirect, render_template, send_file, current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models import db, User, Meeting
from gemini_utils import summarize_with_gemini
from google import genai
from google.genai import types
from .decorators import login_required

meeting_bp = Blueprint('meeting', __name__)

# --- Gemini Setup ---
genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Directory for recordings ---
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# ------------------ TRANSCRIBE & SUMMARIZE ------------------
def transcribe_and_summarize(audio_path: str):
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"),
                " Transcribe this meeting audio(you should transcribe audio in Hinglish if audio is of mix languags.) and return JSON like : " +
                " Transcribe this meeting audio and return JSON with keys transcript, summary, and action_items. Action_items should be a list of objects like: [{\"who\": \"Person\", \"what\": \"Task\", \"when\": \"Date\"}],"
            ]   
        )
        print(" Raw Gemini Response:", response.text.strip())
        raw = response.text.strip()
        cleaned = re.sub(r"^```json|```$", "", raw).strip()
        data = json.loads(cleaned)

        transcript = data.get("transcript", "")
        summary = data.get("summary", "")
        action_items = data.get("action_items", [])
        return transcript, summary, action_items

    except Exception as e:
        print("Error parsing Gemini response:", e)
        return "", "", []

# ------------------ UPLOAD AUDIO ------------------
@meeting_bp.route('/upload_audio', methods=['POST'])
@login_required
def upload_audio():
    if 'audio' not in request.files:
        return jsonify(status="error", error="Audio missing"), 400

    audio = request.files['audio']
    filename = f"{uuid.uuid4()}.webm"
    path = os.path.join(RECORDINGS_DIR, filename)
    audio.save(path)

    transcript, summary, action_items = transcribe_and_summarize(path)

    user = User.query.filter_by(email=session['user']).first()
    meeting = Meeting(
        title=f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        user_id=user.id,
        filename=filename,
        transcript=transcript,
        summary=summary,
        action_items=action_items,
        created_at=datetime.utcnow()
    )
    db.session.add(meeting)
    db.session.commit()

    return jsonify(
        status="success",
        transcript=transcript,
        summary=summary,
        action_items=[str(item) for item in action_items]
    )

# ------------------ DOWNLOAD PDF ------------------
@meeting_bp.route('/download_pdf/<int:meeting_id>')
@login_required
def download_pdf(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin, y = 50, height - 50

    # Fonts
    devanagari_font_path = os.path.join("fonts", "NotoSansDevanagari-Regular.ttf")
    pdfmetrics.registerFont(TTFont("HindiFont", devanagari_font_path))

    eng_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    hindi_font = "HindiFont"
    font_size = 14
    heading_size = 16

    def draw_wrapped_line(line, font, size):
        nonlocal y
        wrapped = simpleSplit(line, font, size, width - 2 * margin)
        for wline in wrapped:
            if y < margin:
                c.showPage()
                y = height - margin
            c.setFont(font, size)
            c.drawString(margin, y, wline)
            y -= 18

    def draw_smart(text):
        nonlocal y
        lines = text.split("\n")
        for line in lines:
            is_hindi = bool(re.search(r'[\u0900-\u097F]', line))
            font = hindi_font if is_hindi else eng_font

            # Check if line is like "Speaker 1: ..."
            match = re.match(r"^(Speaker\s+\d+:)", line)
            if match:
                bold_part = match.group(1)
                rest = line[len(bold_part):].strip()
                if y < margin:
                    c.showPage()
                    y = height - margin
                c.setFont(bold_font, font_size)
                c.drawString(margin, y, bold_part)
                c.setFont(font, font_size)
                c.drawString(margin + c.stringWidth(bold_part, bold_font, font_size) + 4, y, rest)
                y -= 18
            else:
                draw_wrapped_line(line, font, font_size)

    # --- Title ---
    c.setFont(bold_font, heading_size)
    c.drawString(margin, y, f"Meeting: {meeting.title}")
    y -= 30

    # --- Summary ---
    c.setFont(bold_font, heading_size)
    c.drawString(margin, y, "Summary:")
    y -= 24
    draw_smart(meeting.summary or "")
    y -= 30

    # --- Transcript ---
    c.setFont(bold_font, heading_size)
    c.drawString(margin, y, "Transcript:")
    y -= 24
    draw_smart(meeting.transcript or "")
    y -= 30

    # --- Action Items ---
    c.setFont(bold_font, heading_size)
    c.drawString(margin, y, "Action Items:")
    y -= 24

    if meeting.action_items:
        try:
            items = meeting.action_items
            if isinstance(items, str):
                items = json.loads(items)
            for item in items:
                if isinstance(item, dict):
                    who = item.get('who', '')
                    what = item.get('what', '')
                    when = item.get('when', '')

                    for label, value in [('Who', who), ('What', what), ('When', when)]:
                        if y < margin:
                            c.showPage()
                            y = height - margin
                        c.setFont(bold_font, font_size)
                        c.drawString(margin, y, f"{label}:")
                        c.setFont(eng_font, font_size)
                        c.drawString(margin + 50, y, value)
                        y -= 18

                    y -= 12  # extra space between items
                else:
                    draw_wrapped_line(str(item), eng_font, font_size)
        except Exception as e:
            draw_wrapped_line(f"⚠ Failed to parse action items: {str(e)}", eng_font, font_size)
    else:
        draw_wrapped_line("No action items.", eng_font, font_size)

    # Finish PDF
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{meeting.title}.pdf",
        mimetype='application/pdf'
    )




# ------------------ DELETE MEETING ------------------
@meeting_bp.route('/delete/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if session.get('role') != 'admin' and session['user'] != meeting.user.email:
        flash("You are not authorized to delete this meeting.", "danger") 
        return redirect('/dashboard')

    db.session.delete(meeting)
    db.session.commit()
    flash("Meeting deleted successfully.", "success") 
    return redirect('/dashboard')
