import os
import base64
from dotenv import load_dotenv
from github import Github, GithubException
from mcp.server.fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
DEFAULT_OWNER = os.getenv("GITHUB_OWNER", "")
DEFAULT_REPO  = os.getenv("GITHUB_REPO", "")

gh  = Github(GITHUB_TOKEN)
mcp = FastMCP("github-mcp-server")


def _repo(owner: str, repo: str):
    return gh.get_repo(f"{owner}/{repo}")


# ── Repository ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_repo(owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO) -> dict:
    """Get metadata about a GitHub repository."""
    r = _repo(owner, repo)
    return {
        "name": r.name,
        "full_name": r.full_name,
        "description": r.description,
        "default_branch": r.default_branch,
        "private": r.private,
        "url": r.html_url,
        "stars": r.stargazers_count,
        "forks": r.forks_count,
        "open_issues": r.open_issues_count,
        "created_at": str(r.created_at),
        "updated_at": str(r.updated_at),
    }


# ── Branches ──────────────────────────────────────────────────────────────────

@mcp.tool()
def list_branches(owner: str = DEFAULT_OWNER, repo: str = DEFAULT_REPO) -> list[dict]:
    """List all branches in a repository."""
    return [
        {"name": b.name, "sha": b.commit.sha, "protected": b.protected}
        for b in _repo(owner, repo).get_branches()
    ]


@mcp.tool()
def create_branch(
    branch: str,
    from_branch: str = "",
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> str:
    """Create a new branch from an existing branch or SHA."""
    r = _repo(owner, repo)
    source = from_branch or r.default_branch
    sha = r.get_branch(source).commit.sha
    r.create_git_ref(ref=f"refs/heads/{branch}", sha=sha)
    return f"Branch '{branch}' created at {sha}"


# ── Commits ───────────────────────────────────────────────────────────────────

@mcp.tool()
def list_commits(
    branch: str = "",
    limit: int = 20,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> list[dict]:
    """List recent commits on a branch (default: repo's default branch)."""
    r = _repo(owner, repo)
    kwargs = {"sha": branch} if branch else {}
    commits = r.get_commits(**kwargs)
    result = []
    for c in commits[:limit]:
        result.append({
            "sha": c.sha,
            "message": c.commit.message,
            "author": c.commit.author.name if c.commit.author else None,
            "date": str(c.commit.author.date) if c.commit.author else None,
            "url": c.html_url,
        })
    return result


@mcp.tool()
def get_commit(
    sha: str,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> dict:
    """Get full details and diff of a single commit by SHA."""
    c = _repo(owner, repo).get_commit(sha)
    return {
        "sha": c.sha,
        "message": c.commit.message,
        "author": {
            "name": c.commit.author.name if c.commit.author else None,
            "email": c.commit.author.email if c.commit.author else None,
            "date": str(c.commit.author.date) if c.commit.author else None,
        },
        "stats": {
            "additions": c.stats.additions,
            "deletions": c.stats.deletions,
            "total": c.stats.total,
        },
        "files": [
            {
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": (f.patch or "")[:2000],
            }
            for f in c.files
        ],
    }


# ── Files ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_file(
    path: str,
    branch: str = "",
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> str:
    """Read the UTF-8 content of a file from a repository."""
    r = _repo(owner, repo)
    kwargs = {"ref": branch} if branch else {}
    content = r.get_contents(path, **kwargs)
    if isinstance(content, list):
        return "\n".join(f"[dir]  {c.path}" if c.type == "dir" else f"[file] {c.path}" for c in content)
    decoded = base64.b64decode(content.content).decode("utf-8")
    return f"SHA: {content.sha}\nPath: {content.path}\nSize: {content.size} bytes\n\n{decoded}"


@mcp.tool()
def list_directory(
    path: str = "",
    branch: str = "",
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> list[dict]:
    """List files and subdirectories at a path (empty = repo root)."""
    r = _repo(owner, repo)
    kwargs = {"ref": branch} if branch else {}
    contents = r.get_contents(path or "/", **kwargs)
    if not isinstance(contents, list):
        return [{"name": contents.name, "type": contents.type, "path": contents.path, "size": contents.size}]
    return [{"name": c.name, "type": c.type, "path": c.path, "size": c.size} for c in contents]


# ── Write / Commit ────────────────────────────────────────────────────────────

@mcp.tool()
def create_or_update_file(
    path: str,
    content: str,
    message: str,
    branch: str = "",
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> dict:
    """Create or update a file and commit the change."""
    r = _repo(owner, repo)
    kwargs = {"ref": branch} if branch else {}
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    try:
        existing = r.get_contents(path, **kwargs)
        if isinstance(existing, list):
            raise ValueError(f"'{path}' is a directory")
        update_kwargs = {"message": message, "content": encoded, "sha": existing.sha}
        if branch:
            update_kwargs["branch"] = branch
        result = r.update_file(path, **update_kwargs)
        action = "updated"
    except GithubException as e:
        if e.status != 404:
            raise
        create_kwargs = {"message": message, "content": encoded}
        if branch:
            create_kwargs["branch"] = branch
        result = r.create_file(path, **create_kwargs)
        action = "created"

    commit = result["commit"]
    return {
        "action": action,
        "path": path,
        "commit_sha": commit.sha,
        "commit_message": commit.commit.message,
        "commit_url": commit.html_url,
    }


@mcp.tool()
def delete_file(
    path: str,
    message: str,
    branch: str = "",
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> str:
    """Delete a file and commit the deletion."""
    r = _repo(owner, repo)
    kwargs = {"ref": branch} if branch else {}
    existing = r.get_contents(path, **kwargs)
    if isinstance(existing, list):
        raise ValueError(f"'{path}' is a directory")
    delete_kwargs = {"message": message, "sha": existing.sha}
    if branch:
        delete_kwargs["branch"] = branch
    result = r.delete_file(path, **delete_kwargs)
    return f"Deleted '{path}'. Commit: {result['commit'].sha}"


# ── Pull Requests ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_pull_requests(
    state: str = "open",
    limit: int = 20,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> list[dict]:
    """List pull requests. state: 'open', 'closed', or 'all'."""
    prs = _repo(owner, repo).get_pulls(state=state)
    result = []
    for pr in prs[:limit]:
        result.append({
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "author": pr.user.login if pr.user else None,
            "head": pr.head.ref,
            "base": pr.base.ref,
            "created_at": str(pr.created_at),
            "url": pr.html_url,
        })
    return result


@mcp.tool()
def create_pull_request(
    title: str,
    head: str,
    base: str,
    body: str = "",
    draft: bool = False,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> dict:
    """Open a new pull request from head branch into base branch."""
    pr = _repo(owner, repo).create_pull(title=title, body=body, head=head, base=base, draft=draft)
    return {"number": pr.number, "url": pr.html_url, "state": pr.state}


# ── Issues ────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_issues(
    state: str = "open",
    limit: int = 20,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> list[dict]:
    """List issues (excludes pull requests). state: 'open', 'closed', or 'all'."""
    issues = _repo(owner, repo).get_issues(state=state)
    result = []
    for i in issues[:limit]:
        if i.pull_request:
            continue
        result.append({
            "number": i.number,
            "title": i.title,
            "state": i.state,
            "author": i.user.login if i.user else None,
            "labels": [lb.name for lb in i.labels],
            "created_at": str(i.created_at),
            "url": i.html_url,
        })
    return result


# ── Search ────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_code(
    query: str,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> list[dict]:
    """Search for code within a repository using GitHub code search syntax."""
    results = gh.search_code(f"{query} repo:{owner}/{repo}")
    return [
        {"path": r.path, "url": r.html_url, "sha": r.sha}
        for r in results[:20]
    ]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
