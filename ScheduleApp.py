import json
import re
import os
import webbrowser
import hashlib
from bs4 import BeautifulSoup
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ==========================================
# LOGIC CLASS (Fixed & Preserved)
# ==========================================
class ScheduleLogic:
    def __init__(self):
        self.DAY_MAP = {0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat'}
        self.DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    def extract_json_from_html(self, html_content):
        # FIXED: Removed the faulty check that caused the 'function' error
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'var result =' in script.string:
                match = re.search(r'var result = ({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        return None
        return None

    def parse_schedule(self, data):
        class_meetings, exam_meetings = [], []
        target_term_code = data.get('TermToShow')
        terms = data.get('Terms', [])
        for term in terms:
            if term.get('Code') != target_term_code: continue
            for course in term.get('PlannedCourses', []):
                section = course.get('Section')
                if not section: continue
                course_code = section.get('FormattedDisplay', 'Unknown')
                course_name = section.get('Title', 'Unknown')
                display_title = course_code.split('*')
                short_title = f"{display_title[0]}*{display_title[1]}" if len(display_title) >= 2 else course_code
                for meeting in section.get('PlannedMeetings', []):
                    days = meeting.get('Days', [])
                    if not days: continue
                    i_method = meeting.get('InstructionalMethod', 'LEC')
                    is_exam = 'EXAM' in i_method.upper()
                    date_str = meeting.get('Dates', '')
                    start_h, start_m = meeting.get('StartTimeHour'), meeting.get('StartTimeMinute')
                    end_h, end_m = meeting.get('EndTimeHour'), meeting.get('EndTimeMinute')
                    if start_h is None or end_h is None: continue
                    start_decimal, end_decimal = start_h + (start_m / 60.0), end_h + (end_m / 60.0)
                    fmt_time, loc = meeting.get('FormattedTime', ''), meeting.get('MeetingLocation', '')
                    clean_id = short_title.replace('*', '').replace(' ', '_')
                    for d in days:
                        if d in self.DAY_MAP:
                            entry = {
                                'id': clean_id, 'title': f"{short_title} ({i_method})",
                                'full_name': course_name, 'day_idx': d, 'start': start_decimal, 'end': end_decimal,
                                'time_str': fmt_time, 'location': loc, 'date_str': date_str if is_exam else "" 
                            }
                            if is_exam: exam_meetings.append(entry)
                            else: class_meetings.append(entry)
        return class_meetings, exam_meetings

    def generate_grid_html(self, meetings, suffix, title):
        if not meetings: return f"<div class='section-title'><h2>{title}</h2><p>No scheduled sessions found.</p></div>", "", ""
        min_time, max_time = min(m['start'] for m in meetings), max(m['end'] for m in meetings)
        start_hour, end_hour = min(8, int(min_time)), max(17, int(max_time) + 1)
        slot_height = 50 
        
        time_html = ""
        current = start_hour
        while current <= end_hour:
            time_html += f'<div class="time">{current:02d}:00</div>\n'
            if current < end_hour: time_html += f'<div class="time">{current:02d}:30</div>\n'
            current += 1

        has_weekend = any(m['day_idx'] in [0, 6] for m in meetings)
        days_to_show = ([0] if has_weekend else []) + [1, 2, 3, 4, 5] + ([6] if has_weekend else [])
        header_html = '<div class="corner"></div>' + "".join([f'<div class="day-header">{self.DAY_NAMES[d]}</div>' for d in days_to_show])
        day_cols_html = "".join([f'<div class="day-col" id="{self.DAY_MAP[d]}_{suffix}"></div>' for d in days_to_show])
        
        js_calls, unique_ids = "", list(set(m['id'] for m in meetings))
        palette = ["#e8f3fd", "#fff6d9", "#dff7e8", "#f0e8fb", "#fde8e8", "#e0f7fa", "#fff0f5", "#f5f5dc"]
        css_colors = ""
        for i, cid in enumerate(unique_ids):
            color = palette[i % len(palette)]
            css_colors += f"  .{cid} {{ background:{color}; border-left: 4px solid rgba(0,0,0,0.1); }}\n"

        for m in meetings:
            t_clean, loc_clean = m['title'].replace("'", "\\'"), m['location'].replace("'", "\\'")
            if m['date_str']: loc_clean = f"{m['date_str']} <br> {loc_clean}"
            js_calls += f"  addClass('{self.DAY_MAP[m['day_idx']]}_{suffix}', '{t_clean}', {m['start']}, {m['end']}, '{m['time_str']}', '{loc_clean}', '{m['id']}', {start_hour}, {end_hour}, {slot_height});\n"
        
        return f"""<div class="calendar-section"><div class="section-header"><h2>{title}</h2><button class="save-btn" onclick="saveAsImage('capture_{suffix}', '{title}')">📸 Save as Image</button></div><div id="capture_{suffix}" class="capture-wrapper"><div class="grid-container"><div class="grid" style="--start-hour:{start_hour}; --end-hour:{end_hour}; --slot-height:{slot_height}px; --cols:{len(days_to_show)};">{header_html}<div class="time-col">{time_html}</div>{day_cols_html}</div></div></div></div>""", js_calls, css_colors

# ==========================================
# GUI APPLICATION
# ==========================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("University Schedule Converter")
        self.geometry("600x650")
        ctk.set_appearance_mode("dark")
        
        self.logic = ScheduleLogic()
        self.selected_file = None

        self.label = ctk.CTkLabel(self, text="Schedule Converter", font=("Arial", 26, "bold"))
        self.label.pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, width=540, height=480)
        self.tabview.pack(pady=10, padx=20)
        self.tab_convert = self.tabview.add("1. Convert")
        self.tab_help = self.tabview.add("2. How to get Schedule.html")

        # TAB 1
        self.btn_select = ctk.CTkButton(self.tab_convert, text="Select saved Schedule.html", command=self.select_file, height=45, width=300)
        self.btn_select.pack(pady=(50, 5))
        self.lbl_file = ctk.CTkLabel(self.tab_convert, text="No file selected", text_color="gray")
        self.lbl_file.pack()

        self.btn_convert = ctk.CTkButton(self.tab_convert, text="Generate & Open Calendar", state="disabled", fg_color="#3b82f6", hover_color="#2563eb", command=self.process, height=45, width=300)
        self.btn_convert.pack(pady=40)
        self.lbl_status = ctk.CTkLabel(self.tab_convert, text="")
        self.lbl_status.pack()

        # TAB 2
        instr_text = (
            "1. Login to WebAdvisor.\n\n"
            "2. Go to: Academics > Student Planning >\n"
            "   'Plan, Schedule, Register & Drop'\n\n"
            "3. Use arrows to find the correct Semester.\n\n"
            "4. Click the [ Print ] button.\n\n"
            "5. A new 'Print Schedule' tab will open.\n\n"
            "6. In that new tab, press: [ Ctrl + S ] (Win) or [ Cmd + S ] (Mac).\n\n"
            "7. Save as 'Webpage, HTML Only'.\n\n"
            "8. Back in this app, select that file and click Generate!"
        )
        self.help_label = ctk.CTkLabel(self.tab_help, text=instr_text, justify="left", font=("Arial", 13), padx=20)
        self.help_label.pack(pady=20, fill="both")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
        if path:
            self.selected_file = path
            self.lbl_file.configure(text=os.path.basename(path))
            self.btn_convert.configure(state="normal")

    def process(self):
        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                content = f.read()
            data = self.logic.extract_json_from_html(content)
            if not data:
                messagebox.showerror("Error", "Could not find schedule data. Please follow the instructions in Tab 2.")
                return

            classes, exams = self.logic.parse_schedule(data)
            html_classes, js_classes, css_classes = self.logic.generate_grid_html(classes, "cls", "Weekly Classes")
            html_exams, js_exams, css_exams = self.logic.generate_grid_html(exams, "exm", "Final Exams")

            full_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js"></script>
<style>
  :root{{ --bg:#f7f8fb; --left-w:50px; }} * {{ box-sizing: border-box; }}
  body{{ margin:0; padding:0; font-family:sans-serif; background:var(--bg); }}
  .wrap{{ padding-bottom: 50px; max-width: 100%; }}
  header{{ padding: 15px; background: #fff; border-bottom: 1px solid #e5e7eb; text-align: center; margin-bottom: 20px; }}
  .section-header {{ display: flex; justify-content: space-between; align-items: center; padding: 0 16px 10px 16px; }}
  .section-header h2 {{ font-size: 16px; color: #374151; margin: 0; border-left: 4px solid #3b82f6; padding-left: 10px; }}
  .save-btn {{ background:#fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; }}
  .capture-wrapper {{ background: #ffffff; padding: 10px; }}
  .grid-container {{ overflow-x: auto; background: #fff; margin-bottom: 30px; border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb; }}
  .grid{{ display:grid; grid-template-columns: var(--left-w) repeat(var(--cols), minmax(90px, 1fr)); position: relative; min-width: 600px; }}
  .day-header{{ padding:12px 4px; text-align:center; font-weight:600; background:#f9fafb; border-bottom:1px solid #e5e7eb; border-right:1px solid #f3f4f6; font-size:11px; }}
  .time-col {{ background:#fff; border-right:1px solid #e5e7eb; }}
  .time{{ height:var(--slot-height); text-align:right; font-size:10px; color:#9ca3af; transform:translateY(-6px); padding-right:5px; }}
  .day-col{{ position:relative; border-right:1px solid #f3f4f6; background: repeating-linear-gradient(to bottom, transparent, transparent calc(var(--slot-height) - 1px), #f3f4f6 var(--slot-height)); }}
  .class-block{{ position:absolute; left:2px; right:2px; border-radius:5px; padding:4px 5px; font-size:11px; border:1px solid rgba(0,0,0,0.05); box-shadow: 0 1px 2px rgba(0,0,0,0.05); display:flex; flex-direction:column; justify-content:center; }}
  .title{{ font-weight:700; color:#1f2937; }}
{css_classes} {css_exams}
</style></head><body><div class="wrap"><header><h1>Schedule</h1></header>{html_classes}{html_exams}</div>
<script>
function addClass(dayId, title, start, end, timeStr, loc, colorClass, startHour, endHour, slotHeight){{
    const range = endHour - startHour;
    const top = ((start - startHour) / range) * (range * 2 * slotHeight);
    const height = ((end - start) / range) * (range * 2 * slotHeight);
    const el = document.createElement('div'); el.className = `class-block ${{colorClass}}`;
    el.style.top = top + 'px'; el.style.height = (height - 2) + 'px'; 
    el.innerHTML = `<div class="title">${{title}}</div><div style="font-size:10px; color:#4b5563;">${{timeStr}}</div><div style="font-size:9px; color:#6b7280; margin-top:1px;">${{loc}}</div>`;
    document.getElementById(dayId).appendChild(el);
}}
function saveAsImage(id, name) {{
    htmlToImage.toPng(document.getElementById(id), {{ backgroundColor: '#fff', pixelRatio: 2 }})
    .then(url => {{ var l = document.createElement('a'); l.download = name+'.png'; l.href = url; l.click(); }});
}}
{js_classes} {js_exams}
</script></body></html>"""

            output_path = os.path.join(os.path.dirname(self.selected_file), "my_calendar.html")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)

            self.lbl_status.configure(text="✅ Success! Opening browser...", text_color="#2ecc71")
            webbrowser.open('file://' + os.path.realpath(output_path))
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    app = App()
    app.mainloop()