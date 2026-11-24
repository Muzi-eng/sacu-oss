\# SACU OSS - Integrated REST-Based One Stop Shop



Demonstration of a REST-based One Stop Shop gateway that automates

cross-border declarations and payments between Eswatini Revenue Service (ERS),

South African Revenue Service (SARS) and Revenue Services Lesotho (RSL).



\## Requirements

\- Python 3.10+

\- pip



\## Setup

python -m venv .venv

.venv\\Scripts\\activate

pip install -r requirements.txt





\## Run

python run\_all.py



Opens:

\- Gateway (API + portal): http://127.0.0.1:8000

\- API docs: http://127.0.0.1:8000/docs

\- ERS: http://127.0.0.1:8001/health

\- SARS: http://127.0.0.1:8002/health

\- RSL: http://127.0.0.1:8003/health



\## Demo

python demo\_client.py





\## Limitations

\- Simulated integrations (not connected to real ASYCUDA or SARS systems)

\- Illustrative duty and VAT rates

\- API key authentication only

