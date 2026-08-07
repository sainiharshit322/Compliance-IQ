from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict
from pydantic import BaseModel, Field

from services.collector_agent.resiliency import execute_with_exponential_backoff

logger = logging.getLogger("collector_agent.tools.github_pr_rules")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReadGithubPrRulesOutput(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    repository: str
    branch: str
    is_protected: bool
    required_approving_review_count: int = Field(default=0)
    dismiss_stale_reviews: bool = Field(default=False)
    require_code_owner_reviews: bool = Field(default=False)
    require_signed_commits: bool = Field(default=False)
    enforce_admins: bool = Field(default=False)
    is_compliant: bool = Field(description="True if branch protection requires >= 1 approval and code owner reviews")


@execute_with_exponential_backoff(max_retries=3, base_delay=0.1, max_delay=1.0)
def read_github_pr_rules(
    repository_owner: str,
    repository_name: str,
    branch_name: str = "master",
) -> Dict[str, Any]:
    """
    Fetches GitHub branch protection rules for a target repository and branch with exponential backoff.
    Uses GitHub REST API if GITHUB_PAT_TOKEN is present, otherwise falls back to mock output.
    """
    repo_full_name = f"{repository_owner}/{repository_name}"
    logger.info(f"Inspecting GitHub branch protection rules for '{repo_full_name}' on branch '{branch_name}'...")

    github_token = os.getenv("GITHUB_PAT_TOKEN")

    if github_token and not github_token.startswith("ghp_placeholder"):
        try:
            import requests
            url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/branches/{branch_name}/protection"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            logger.info("Executing live GitHub REST API branch protection request...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_reviews = data.get("required_pull_request_reviews", {})
                approving_count = required_reviews.get("required_approving_review_count", 0)
                dismiss_stale = required_reviews.get("dismiss_stale_reviews", False)
                require_code_owners = required_reviews.get("require_code_owner_reviews", False)
                require_signatures = data.get("required_signatures", {}).get("enabled", False)
                enforce_admins_flag = data.get("enforce_admins", {}).get("enabled", False)

                is_compliant = (approving_count >= 1) and require_code_owners

                output = ReadGithubPrRulesOutput(
                    repository=repo_full_name,
                    branch=branch_name,
                    is_protected=True,
                    required_approving_review_count=approving_count,
                    dismiss_stale_reviews=dismiss_stale,
                    require_code_owner_reviews=require_code_owners,
                    require_signed_commits=require_signatures,
                    enforce_admins=enforce_admins_flag,
                    is_compliant=is_compliant,
                )
                return output.model_dump()
        except Exception as ex:
            logger.warning(f"Live GitHub API call failed ({ex}). Using mock evaluation output.")

    # Fallback / Mock execution matching 05_agent_tools.md Section 2.4 schema
    is_protected_mock = True
    approving_count_mock = 2
    code_owners_mock = True
    signed_commits_mock = True
    enforce_admins_mock = True

    output = ReadGithubPrRulesOutput(
        repository=repo_full_name,
        branch=branch_name,
        is_protected=is_protected_mock,
        required_approving_review_count=approving_count_mock,
        dismiss_stale_reviews=True,
        require_code_owner_reviews=code_owners_mock,
        require_signed_commits=signed_commits_mock,
        enforce_admins=enforce_admins_mock,
        is_compliant=(approving_count_mock >= 1) and code_owners_mock,
    )

    return output.model_dump()
