================================================================================
CSC411 INTEGRATIVE PROGRAMMING TECHNOLOGIES - MINI PROJECT
An Integrated REST-Based One Stop Shop for Declaring and Paying for 
Imports and Exports between Eswatini, South Africa and Lesotho
================================================================================

TEAM MEMBERS
--------------------------------------------------------------------------------
Name                  Student Number    GitHub Profile
Muzi Mncwanga         202302925         https://github.com/Muzi-eng
Ntshingila Mzwandile  202302667         https://github.com/mzwandilentshingila
Dlamini Sibusiso      202303067         https://github.com/Sibusiso-sd
Mlamuli Sibandze      202305050         https://github.com/BhutiiMlamuli

GITHUB REPOSITORY
--------------------------------------------------------------------------------
https://github.com/Muzi-eng/sacu-oss

CONTENTS OF THIS SUBMISSION
--------------------------------------------------------------------------------
1. CSC411_Mini_Project_Report_Final.pdf
   - The full project report (Introduction, Requirement Analysis, System Design, 
     Implementation Details, Conclusion, References).

2. CSC411_SACU_OSS_Presentation.pptx
   - The presentation slides for the video walkthrough.

3. CSC411_SACU_OSS_Video.mp4
   - The 8-10 minute recorded presentation and live demo. (Included separately)

4. source_code/ 
   - The complete source code for the integrated system.

HOW TO RUN THE SYSTEM
--------------------------------------------------------------------------------
Requirements: Python 3.10+ installed on your machine.

1. Open a terminal and navigate to the source code folder:
   cd source_code

2. Create and activate a virtual environment:
   python -m venv .venv
   .venv\Scripts\activate    (On Windows)
   source .venv/bin/activate (On Mac/Linux)

3. Install dependencies:
   pip install -r requirements.txt

4. Start the 4 services (Gateway, ERS, SARS, RSL):
   python run_all.py

5. Open the web portal in your browser:
   http://127.0.0.1:8000/

6. To run the automated demo script (in a second terminal):
   .venv\Scripts\activate
   python demo_client.py
================================================================================