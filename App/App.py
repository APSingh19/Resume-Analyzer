# Developed by dnoobnerd [https://dnoobnerd.netlify.app]    Made with Streamlit


###### Packages Used ######
import streamlit as st  # core package used in this project
import pandas as pd
import base64
import random
import time
import datetime
import pymysql
import os
import re
import socket
import platform
import geocoder
import secrets
import io
import random
import plotly.express as px  # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import nltk
nltk.download('stopwords')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'Uploaded_Resumes')
os.makedirs(UPLOAD_DIR, exist_ok=True)


###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    # bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(
        resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    # close open handles
    converter.close()
    fake_file_handle.close()

    # Extract names using regex (this is a simple example)
    # Adjust the regex pattern according to your needs
    names = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', text)

    # Return the extracted names
    return names


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    # slider to choose from range 1-10
    no_of_reco = st.slider(
        'Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


def get_config_value(key, default=""):
    try:
        return st.secrets[key]
    except (FileNotFoundError, KeyError):
        return os.getenv(key, default)


# sql connector
connection = pymysql.connect(
    host=get_config_value('MYSQL_HOST', 'localhost'),
    user=get_config_value('MYSQL_USER', 'root'),
    password=get_config_value('MYSQL_PASSWORD', ''),
    db=get_config_value('MYSQL_DATABASE', 'VC'),
    port=int(get_config_value('MYSQL_PORT', '3306')),
)
cursor = connection.cursor()


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country, act_name, act_mail, act_mob, name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses, pdf_name):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (str(sec_token), str(ip_add), host_name, dev_user, os_name_ver, str(latlong), city, state, country, act_name, act_mail, act_mob,
                  name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses, pdf_name)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name, feed_email, feed_score, comments, Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon=os.path.join(BASE_DIR, 'Logo', 'recommend.png'),
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_global_styles():
    st.markdown(
        """
        <style>
            :root {
                --brand: #2563eb;
                --brand-dark: #1e3a8a;
                --ink: #172033;
                --muted: #64748b;
                --line: #e2e8f0;
                --surface: #ffffff;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 30rem),
                    linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
                color: var(--ink);
            }

            header[data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0.86);
                backdrop-filter: blur(12px);
                border-bottom: 1px solid rgba(226, 232, 240, 0.8);
            }

            section[data-testid="stSidebar"] {
                background: #0f172a;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }

            section[data-testid="stSidebar"] * {
                color: #e5edf8 !important;
            }

            section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 8px;
            }

            .block-container {
                padding-top: 2rem;
                max-width: 1180px;
            }

            .app-hero {
                background: linear-gradient(135deg, #ffffff 0%, #eef5ff 100%);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 28px 32px;
                margin-bottom: 24px;
                box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            }

            .app-eyebrow {
                color: var(--brand);
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0;
                margin-bottom: 8px;
                text-transform: uppercase;
            }

            .app-title {
                color: var(--ink);
                font-size: 40px;
                font-weight: 800;
                line-height: 1.12;
                margin: 0 0 10px;
            }

            .app-subtitle {
                color: var(--muted);
                font-size: 17px;
                line-height: 1.6;
                margin: 0;
                max-width: 760px;
            }

            .hero-metrics {
                display: grid;
                gap: 14px;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                margin-top: 24px;
            }

            .metric-tile {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 16px;
            }

            .metric-value {
                color: var(--ink);
                font-size: 24px;
                font-weight: 800;
                line-height: 1;
                margin-bottom: 6px;
            }

            .metric-label {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.35;
            }

            .sidebar-brand {
                border-bottom: 1px solid rgba(255, 255, 255, 0.12);
                margin: 0 0 20px;
                padding-bottom: 18px;
            }

            .sidebar-logo {
                color: #ffffff;
                font-size: 22px;
                font-weight: 800;
                line-height: 1.15;
            }

            .sidebar-caption {
                color: #9fb4d0 !important;
                font-size: 13px;
                line-height: 1.45;
                margin-top: 8px;
            }

            .page-heading {
                margin: 8px 0 20px;
            }

            .page-heading h2 {
                font-size: 28px;
                margin: 0 0 6px;
            }

            .page-heading p {
                color: var(--muted);
                font-size: 15px;
                margin: 0;
            }

            .soft-panel {
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid var(--line);
                border-radius: 8px;
                box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
                margin: 16px 0;
                padding: 20px 22px;
            }

            .section-kicker {
                color: var(--brand);
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0;
                margin-bottom: 4px;
                text-transform: uppercase;
            }

            .info-note {
                color: var(--muted);
                font-size: 14px;
                line-height: 1.55;
                margin: 0 0 10px;
            }

            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 14px 16px;
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
            }

            .stTextInput input,
            .stTextArea textarea {
                border-radius: 8px;
                border: 1px solid #cbd5e1;
            }

            .stButton > button,
            .stDownloadButton > button,
            button[kind="primaryFormSubmit"] {
                background: var(--brand);
                border: 1px solid var(--brand);
                border-radius: 8px;
                color: white;
                font-weight: 700;
                min-height: 42px;
                box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            button[kind="primaryFormSubmit"]:hover {
                background: var(--brand-dark);
                border-color: var(--brand-dark);
                color: white;
            }

            div[data-testid="stFileUploader"] section {
                background: var(--surface);
                border: 1px dashed #93c5fd;
                border-radius: 8px;
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stPlotlyChart"] {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 10px;
            }

            h1, h2, h3 {
                color: var(--ink);
                letter-spacing: 0;
            }

            .stAlert {
                border-radius: 8px;
            }

            @media (max-width: 760px) {
                .app-title {
                    font-size: 32px;
                }

                .hero-metrics {
                    grid-template-columns: 1fr;
                }
            }

            #MainMenu, footer {
                visibility: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    st.markdown(
        """
        <div class="app-hero">
            <div class="app-eyebrow">Resume intelligence platform</div>
            <h1 class="app-title">AI Resume Analyzer</h1>
            <p class="app-subtitle">
                Upload a resume to extract candidate details, evaluate profile strength,
                recommend skills, and review analytics from a clean recruiter-ready dashboard.
            </p>
            <div class="hero-metrics">
                <div class="metric-tile">
                    <div class="metric-value">PDF</div>
                    <div class="metric-label">Resume parsing and profile extraction</div>
                </div>
                <div class="metric-tile">
                    <div class="metric-value">100</div>
                    <div class="metric-label">Resume score with practical improvement checks</div>
                </div>
                <div class="metric-tile">
                    <div class="metric-value">Admin</div>
                    <div class="metric-label">Candidate analytics and feedback dashboard</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_heading(title, subtitle):
    st.markdown(
        f"""
        <div class="page-heading">
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_soft_panel(kicker, title, body):
    st.markdown(
        f"""
        <div class="soft-panel">
            <div class="section-kicker">{kicker}</div>
            <h3>{title}</h3>
            <p class="info-note">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


###### Main function run() ######


def run():
    apply_global_styles()
    render_app_header()

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">AI Resume Analyzer</div>
            <div class="sidebar-caption">Resume screening, recommendations, feedback, and analytics in one workspace.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("## Navigation")
    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox(
        "Choose a workspace", activities)
    link = '<span style="color:#9fb4d0;">Built by Himanshi & Agam</span>'
    # link = '<b>Built with 🤍 by <a href="https://dnoobnerd.netlify.app/" style="text-decoration: none; color: #021659;">Himanshi & Agam </a></b>'
    st.sidebar.markdown(link, unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="sidebar-caption">Local MySQL connected. Streamlit dashboard ready.</p>',
        unsafe_allow_html=True,
    )

    ###### Creating Database and Table ######

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)

    # Create table user_data and user_feedback
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL,
                    PRIMARY KEY (ID)
                    );
                """
    cursor.execute(table_sql)

    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    cursor.execute(tablef_sql)

    ###### CODE FOR CLIENT SIDE (USER) ######
    if choice == 'User':
        render_page_heading(
            "Analyze a Resume",
            "Enter candidate details, upload a PDF resume, and generate role, skill, score, and course recommendations.",
        )
        render_soft_panel(
            "Candidate intake",
            "Profile details",
            "These fields identify the candidate record saved in the admin dashboard.",
        )

        # Collecting Miscellaneous Information
        col_name, col_email, col_mobile = st.columns(3)
        with col_name:
            act_name = st.text_input('Full name', placeholder='Candidate name')
        with col_email:
            act_mail = st.text_input('Email address', placeholder='name@example.com')
        with col_mobile:
            act_mob = st.text_input('Mobile number', placeholder='10 digit number')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')
        city = cityy
        state = statee
        country = countryy

        render_soft_panel(
            "Resume upload",
            "Upload PDF resume",
            "The analyzer will extract contact information, skills, education signals, resume score, and personalized recommendations.",
        )

        # file upload in pdf format
        pdf_file = st.file_uploader("Select resume PDF", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)

            # saving the uploaded resume to folder
            save_image_path = os.path.join(UPLOAD_DIR, pdf_file.name)
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            # parsing and extracting whole resume
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:

                # Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                # Showing Analyzed data from (resume_data)
                render_page_heading(
                    "Resume Analysis",
                    "Here is the extracted candidate profile and the first-pass resume assessment.",
                )
                st.header("**Resume Analysis 🤘**")
                st.success("Analysis completed for " + resume_data['name'])
                st.subheader("**Your Basic info 👀**")
                try:
                    info_col1, info_col2, info_col3 = st.columns(3)
                    info_col1.metric("Name", resume_data['name'])
                    info_col2.metric("Email", resume_data['email'])
                    info_col3.metric("Contact", resume_data['mobile_number'])
                    info_col4, info_col5 = st.columns(2)
                    info_col4.metric("Degree", str(resume_data['degree']))
                    info_col5.metric("Resume pages", str(resume_data['no_of_pages']))

                except:
                    pass
                # Predicting Candidate Experience Level

                # Trying with different possibilities
                cand_level = ''
                if resume_data['no_of_pages'] < 1:
                    cand_level = "NA"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''', unsafe_allow_html=True)

                # if internship then intermediate level
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)

                # if Work Experience/Experience then Experience level
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''', unsafe_allow_html=True)

                # Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")

                # Current Analyzed Skills
                keywords = st_tags(label='### Your Current Skills',
                                   text='See our skills recommendation below', value=resume_data['skills'], key='1  ')

                # Keywords for Recommendations
                ds_keyword = ['tensorflow', 'keras', 'pytorch',
                              'machine learning', 'deep Learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel',
                               'magento', 'wordpress', 'javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = [
                    'android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development',
                               'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']
                n_any = ['english', 'communication', 'writing', 'microsoft office',
                         'leadership', 'customer management', 'social media']
                # Skill Recommendations Starts
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                # condition starts to check skills from keywords and predict field
                for i in resume_data['skills']:

                    # Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success(
                            "** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask", 'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='2')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    # Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success(
                            "** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel',
                                              'Magento', 'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='3')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    # Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success(
                            "** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter',
                                              'Kotlin', 'XML', 'Java', 'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='4')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    # IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success(
                            "** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation', 'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='5')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    # Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success(
                            "** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq', 'Prototyping', 'Wireframes', 'Storyframes',
                                              'Adobe Photoshop', 'Editing', 'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe', 'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='6')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    # For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning(
                            "** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Currently No Recommendations', value=recommended_skills, key='6')
                        st.markdown(
                            '''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''', unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break

                # Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                resume_score = 0

                # Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''', unsafe_allow_html=True)

                if 'Education' or 'School' or 'College' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>''', unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''', unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>''', unsafe_allow_html=True)

                if 'INTERNSHIPS' in resume_text:
                    resume_score = resume_score + 6
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''', unsafe_allow_html=True)
                elif 'INTERNSHIP' in resume_text:
                    resume_score = resume_score + 6
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''', unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    resume_score = resume_score + 6
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''', unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    resume_score = resume_score + 6
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>''', unsafe_allow_html=True)

                if 'SKILLS' in resume_text:
                    resume_score = resume_score + 7
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''', unsafe_allow_html=True)
                elif 'SKILL' in resume_text:
                    resume_score = resume_score + 7
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''', unsafe_allow_html=True)
                elif 'Skills' in resume_text:
                    resume_score = resume_score + 7
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''', unsafe_allow_html=True)
                elif 'Skill' in resume_text:
                    resume_score = resume_score + 7
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Skills. It will help you a lot</h4>''', unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''', unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''', unsafe_allow_html=True)

                if 'INTERESTS' in resume_text:
                    resume_score = resume_score + 5
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''', unsafe_allow_html=True)
                elif 'Interests' in resume_text:
                    resume_score = resume_score + 5
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Interest. It will show your interest other that job.</h4>''', unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''', unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''', unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''', unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''', unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>''', unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''', unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''', unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''', unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown(
                        '''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''', unsafe_allow_html=True)

                st.subheader("**Resume Score 📝**")

                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                # Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                # Score
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have in your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                # Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(
                    ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(
                    ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                # Calling insert_data to add all the data into user_data
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(
                    resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                # Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                # Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                # On Successful Result
                st.balloons()

            else:
                st.error('Something went wrong..')

    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':
        render_page_heading(
            "Feedback Center",
            "Capture user feedback and review satisfaction trends from previous submissions.",
        )

        # timestamp
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.subheader("Submit Feedback")
            feed_col1, feed_col2 = st.columns(2)
            with feed_col1:
                feed_name = st.text_input('Name')
            with feed_col2:
                feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments', placeholder='Share what worked well or what should improve')
            Timestamp = timestamp
            submitted = st.form_submit_button("Submit")
            if submitted:
                # Calling insertf_data to add dat into user feedback
                insertf_data(feed_name, feed_email,
                             feed_score, comments, Timestamp)
                # Success Message
                st.success("Thanks! Your Feedback was recorded.")
                # On Successful Submit
                st.balloons()

        # query to fetch data from user feedback table
        query = 'select * from user_feedback'
        plotfeed_data = pd.read_sql(query, connection)

        # fetching feed_score from the query and getting the unique values and total value count
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()

        # plotting pie chart for user ratings
        st.subheader("Rating Distribution")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5",
                     color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)

        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("Recent Comments")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])
        st.dataframe(dff, width=1000)

    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':
        render_page_heading(
            "About",
            "A practical resume analysis tool for applicants, recruiters, and placement teams.",
        )

        st.subheader("Platform Overview")

        st.markdown('''

        <p align='justify'>
            A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant based on keyword matching.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>User -</b> <br/>
            In the Side Bar choose yourself as user and fill the required fields and upload your resume in pdf format.<br/>
            Just sit back and relax our tool will do the magic on it's own.<br/><br/>
            <b>Feedback -</b> <br/>
            A place where user can suggest some feedback about the tool.<br/><br/>
            <b>Admin -</b> <br/>
            For login use <b>Agam</b> as username and <b>Himanshi</b> as password.<br/>
            It will load all the required stuffs and perform analysis.
        </p><br/><br/>

        <p align="justify">
            Built with 🤍 by 
            <a href="url" style="text-decoration: none; color: grey;">Agam & Himanshi</a> 
        </p>

        ''', unsafe_allow_html=True)

    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        render_page_heading(
            "Admin Dashboard",
            "Review candidate submissions, feedback, resume scores, locations, and recommendation analytics.",
        )
        st.info('Enter admin credentials to view protected analytics.')

        #  Admin Login
        login_col1, login_col2 = st.columns(2)
        with login_col1:
            ad_user = st.text_input("Username")
        with login_col2:
            ad_password = st.text_input("Password", type='password')

        if st.button('Login'):

            # Credentials
            if ad_user == 'Agam' and ad_password == 'Himanshi':

                # Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute(
                    '''SELECT ID, ip_add, resume_score, convert(Predicted_Field using utf8), convert(User_level using utf8), city, state, country from user_data''')
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(datanalys, columns=[
                                         'Idt', 'IP_add', 'resume_score', 'Predicted_Field', 'User_Level', 'City', 'State', 'Country'])

                # Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success("Welcome Himanshi ! Total %d " %
                           values + " User's Have Used Our Tool : )")

                # Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute('''SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, convert(Predicted_Field using utf8), Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, convert(User_level using utf8), convert(Actual_skills using utf8), convert(Recommended_skills using utf8), convert(Recommended_courses using utf8), city, state, country, latlong, os_name_ver, host_name, dev_user from user_data''')
                data = cursor.fetchall()

                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Token', 'IP Address', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                 'Predicted Name', 'Predicted Mail', 'Resume Score', 'Total Page',  'File Name',
                                                 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                 'City', 'State', 'Country', 'Lat Long', 'Server OS', 'Server Name', 'Server User',])

                # Viewing the dataframe
                st.dataframe(df)

                # Downloading Report of user_data in csv file
                st.markdown(get_csv_download_link(df, 'User_Data.csv',
                            'Download Report'), unsafe_allow_html=True)

                # Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute('''SELECT * from user_feedback''')
                data = cursor.fetchall()

                st.header("**User's Feedback Data**")
                df = pd.DataFrame(data, columns=[
                                  'ID', 'Name', 'Email', 'Feedback Score', 'Comments', 'Timestamp'])
                st.dataframe(df)

                # query to fetch data from user_feedback(table)
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, connection)

                # Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()

                # Pie chart for user ratings
                st.subheader("**User Rating's**")
                fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5 🤗",
                             color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)

                # fetching Predicted_Field from the query and getting the unique values and total value count
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for predicted field recommendations
                st.subheader(
                    "**Pie-Chart for Predicted Field Recommendation**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills 👽',
                             color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for User's👨‍💻 Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level",
                             color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count
                labels = plot_data.resume_score.unique()
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Score
                st.subheader("**Pie-Chart for Resume Score**")
                fig = px.pie(df, values=values, names=labels, title='From 1 to 100 💯',
                             color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig)

                # fetching IP_add from the query and getting the unique values and total value count
                labels = plot_data.IP_add.unique()
                values = plot_data.IP_add.value_counts()

                # Pie chart for Users
                st.subheader("**Pie-Chart for Users App Used Count**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based On IP Address 👥',
                             color_discrete_sequence=px.colors.sequential.matter_r)
                st.plotly_chart(fig)

                # fetching City from the query and getting the unique values and total value count
                labels = plot_data.City.unique()
                values = plot_data.City.value_counts()

                # Pie chart for City
                st.subheader("**Pie-Chart for City**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based On City 🌆',
                             color_discrete_sequence=px.colors.sequential.Jet)
                st.plotly_chart(fig)

                # fetching State from the query and getting the unique values and total value count
                labels = plot_data.State.unique()
                values = plot_data.State.value_counts()

                # Pie chart for State
                st.subheader("**Pie-Chart for State**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based on State 🚉',
                             color_discrete_sequence=px.colors.sequential.PuBu_r)
                st.plotly_chart(fig)

                # fetching Country from the query and getting the unique values and total value count
                labels = plot_data.Country.unique()
                values = plot_data.Country.value_counts()

                # Pie chart for Country
                st.subheader("**Pie-Chart for Country**")
                fig = px.pie(df, values=values, names=labels, title='Usage Based on Country 🌏',
                             color_discrete_sequence=px.colors.sequential.Purpor_r)
                st.plotly_chart(fig)

            # For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")


# Calling the main (run()) function to make the whole process run
run()
