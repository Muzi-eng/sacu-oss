import multiprocessing, time, uvicorn

def run_admin(code, port):
    from sacu_oss.admin_service.app import create_app
    app = create_app(code)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

def run_gateway():
    from sacu_oss.oss_gateway.app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    procs = [
        multiprocessing.Process(target=run_admin, args=("ERS", 8001)),
        multiprocessing.Process(target=run_admin, args=("SARS", 8002)),
        multiprocessing.Process(target=run_admin, args=("RSL", 8003)),
        multiprocessing.Process(target=run_gateway),
    ]
    for p in procs:
        p.start()
    time.sleep(2)
    print("Started: ERS 8001 | SARS 8002 | RSL 8003 | Gateway 8000")
    print("Portal: http://127.0.0.1:8000/docs")
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()