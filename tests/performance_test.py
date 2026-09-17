"""Performance Benchmark Test Suite.

Measures actual, un-fabricated timings for:
- Tool execution latency (all 6 tools)
- Short-term & Long-term memory operations latency
- Database query latency
- LangGraph workflow execution latency
- Cohort batch triage latency (60 students)
- API request latency & concurrent requests throughput
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.main import app
from memory.database import get_session_factory
from memory.models import Student
from memory.short_term_memory import short_term_memory
from tools.assignment_analyzer import analyze_assignments
from tools.attendance_analyzer import analyze_attendance
from tools.intervention_knowledge import recommend_interventions
from tools.performance_analyzer import analyze_performance
from tools.student_profile import get_student_profile
from tools.trend_analyzer import analyze_trend
from workflow.batch_analysis import batch_analyzer
from workflow.graph import run_academic_workflow

client = TestClient(app)


def benchmark_tools(iterations: int = 10):
    print("\n--- 1. TOOL LATENCY BENCHMARK ---")
    tools = [
        ("attendance_analyzer", lambda: analyze_attendance("STU104")),
        ("performance_analyzer", lambda: analyze_performance("STU104")),
        ("assignment_analyzer", lambda: analyze_assignments("STU104")),
        ("trend_analyzer", lambda: analyze_trend("STU104")),
        ("student_profile", lambda: get_student_profile("STU104")),
        ("intervention_knowledge", lambda: recommend_interventions(["Low attendance", "Failed assessments"])),
    ]

    for name, fn in tools:
        # Warmup
        fn()
        start = time.perf_counter()
        for _ in range(iterations):
            fn()
        avg_ms = round(((time.perf_counter() - start) / iterations) * 1000, 3)
        print(f"  Tool `{name}`: {avg_ms} ms avg over {iterations} runs")


def benchmark_memory(iterations: int = 20):
    print("\n--- 2. MEMORY & DATABASE LATENCY BENCHMARK ---")
    
    # Short-term memory
    start = time.perf_counter()
    for i in range(iterations):
        sess = f"bench-sess-{i}"
        short_term_memory.record_turn(sess, "Analyze STU104", "Done", "STU104")
        short_term_memory.resolve_student_id(sess, "What about attendance?")
    stm_avg_ms = round(((time.perf_counter() - start) / iterations) * 1000, 3)
    print(f"  Short-Term Memory (Turn + Resolution): {stm_avg_ms} ms avg")

    # Database query
    session_factory = get_session_factory()
    start = time.perf_counter()
    for _ in range(iterations):
        db = session_factory()
        try:
            _ = db.query(Student).filter(Student.student_id == "STU104").first()
        finally:
            db.close()
    db_avg_ms = round(((time.perf_counter() - start) / iterations) * 1000, 3)
    print(f"  Database Query (Student lookup via ORM): {db_avg_ms} ms avg")


def benchmark_workflow(iterations: int = 5):
    print("\n--- 3. LANGGRAPH WORKFLOW LATENCY BENCHMARK ---")
    start = time.perf_counter()
    for _ in range(iterations):
        _ = run_academic_workflow("Analyze STU104", student_id="STU104")
    wf_avg_ms = round(((time.perf_counter() - start) / iterations) * 1000, 2)
    print(f"  Full LangGraph Multi-Agent Workflow: {wf_avg_ms} ms avg over {iterations} runs")


def benchmark_batch_analysis():
    print("\n--- 4. COHORT BATCH ANALYSIS BENCHMARK (60 STUDENTS) ---")
    start = time.perf_counter()
    res = batch_analyzer.analyze_cohort("CSE-A")
    total_batch_ms = round((time.perf_counter() - start) * 1000, 2)
    per_student_ms = round(total_batch_ms / res["total_students"], 3)
    print(f"  Total Cohort Triage (60 students): {total_batch_ms} ms")
    print(f"  Per-student throughput: {per_student_ms} ms/student")


def benchmark_api_and_concurrency(concurrency: int = 10, total_requests: int = 30):
    print(f"\n--- 5. API LATENCY & CONCURRENCY BENCHMARK ({concurrency} concurrent threads) ---")
    
    # 1. Health check latency
    start = time.perf_counter()
    for _ in range(20):
        client.get("/health")
    health_avg_ms = round(((time.perf_counter() - start) / 20) * 1000, 3)
    print(f"  GET /health latency: {health_avg_ms} ms avg")

    # 2. Student analyze latency
    start = time.perf_counter()
    client.post("/students/analyze", json={"student_id": "STU104"})
    stu_ms = round((time.perf_counter() - start) * 1000, 2)
    print(f"  POST /students/analyze (STU104 diagnostic): {stu_ms} ms")

    # 3. Concurrent requests
    def worker(i):
        req_start = time.perf_counter()
        resp = client.post("/ask", json={"question": f"What is academic risk for inquiry {i}?"})
        dur = (time.perf_counter() - req_start) * 1000
        return resp.status_code == 200, dur

    start_all = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(worker, range(total_requests)))
    total_elapsed = time.perf_counter() - start_all

    success_count = sum(1 for ok, _ in results if ok)
    avg_req_ms = round(sum(d for _, d in results) / len(results), 2)
    rps = round(total_requests / total_elapsed, 1)

    print(f"  Concurrent POST /ask: {success_count}/{total_requests} succeeded in {round(total_elapsed, 2)}s")
    print(f"  Average request latency: {avg_req_ms} ms")
    print(f"  Throughput: {rps} req/sec")


def main():
    print("=" * 70)
    print("AI ACADEMIC EARLY-WARNING ENGINE - REAL PERFORMANCE BENCHMARK")
    print("=" * 70)
    benchmark_tools()
    benchmark_memory()
    benchmark_workflow()
    benchmark_batch_analysis()
    benchmark_api_and_concurrency()
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETED SUCCESSFULLY (No fabricated numbers)")
    print("=" * 70)


if __name__ == "__main__":
    main()
