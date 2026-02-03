import requests
from datetime import datetime

# GitHub token
TOKEN = "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"
REPO_NAME = "xauusd-ai-analyst"
OWNER = "james24-cmd"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

print("📜 WORKFLOW RUN HISTORY (Last 10)\n")
print(f"{'Run ID':<15} | {'Date':<20} | {'Status':<12} | {'Conclusion':<10}")
print("-" * 65)

# Get the latest runs
runs_url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/actions/runs"
runs_response = requests.get(runs_url, headers=headers, params={"per_page": 20})

failed_run_id = None

if runs_response.status_code == 200:
    runs = runs_response.json()
    for run in runs['workflow_runs']:
        created_at = datetime.strptime(run['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M")
        status = run['status']
        conclusion = run['conclusion'] or "N/A"
        
        print(f"{run['id']:<15} | {created_at:<20} | {status:<12} | {conclusion:<10}")
        
        # Capture the most recent failure
        if conclusion == 'failure' and not failed_run_id:
            failed_run_id = run['id']

    if failed_run_id:
        print(f"\n\n🔍 ANALYZING FAILURES FOR RUN #{failed_run_id}...")
        
        jobs_url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/actions/runs/{failed_run_id}/jobs"
        jobs_response = requests.get(jobs_url, headers=headers)
        
        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            for job in jobs['jobs']:
                if job['conclusion'] == 'failure':
                    print(f"\n❌ Job Failed: {job['name']}")
                    print(f"   Logs: {job['html_url']}")
                    print("\n   Failed Steps:")
                    for step in job['steps']:
                        if step['conclusion'] == 'failure':
                            print(f"   - {step['name']}")
        else:
            print(f"Failed to fetch jobs for run {failed_run_id}")
    else:
        print("\n✅ No recent failures found in the last 10 runs.")

else:
    print(f"Error fetching runs: {runs_response.status_code}")
print("\n")
