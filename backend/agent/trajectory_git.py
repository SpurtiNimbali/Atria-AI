"""
Git-Style Care Trajectory System

Concepts:
- Commit = discrete state update (vitals, medication change, symptom)
- Branch = alternative care path ("what if we try X?")
- Diff = what changed between two points
- Merge = adopt a branch as the new main path
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib

@dataclass
class Commit:
    """A discrete update to patient state (like a git commit)."""
    commit_id: str
    timestamp: str
    author: str  # "system" or "clinician" or "family"
    message: str  # Human-readable commit message
    state_changes: Dict[str, Any]  # What changed
    parent_commit_id: Optional[str] = None
    branch: str = "main"
    
    def short_id(self) -> str:
        """First 7 chars of commit ID (like git)."""
        return self.commit_id[:7]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.commit_id,
            "short_id": self.short_id(),
            "timestamp": self.timestamp,
            "author": self.author,
            "message": self.message,
            "changes": self.state_changes,
            "parent": self.parent_commit_id,
            "branch": self.branch
        }


@dataclass
class Branch:
    """A care trajectory branch (alternative path)."""
    name: str
    forked_from: str  # commit_id where branch started
    head: str  # latest commit_id in this branch
    description: str
    created_at: str
    probability: float = 1.0  # How likely is this path
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "forked_from": self.forked_from,
            "head": self.head,
            "description": self.description,
            "created_at": self.created_at,
            "probability": self.probability
        }


@dataclass
class PatientState:
    """Current state of patient (like working directory in git)."""
    patient_id: str
    current_branch: str = "main"
    state: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, changes: Dict[str, Any]):
        """Apply changes to state."""
        self.state.update(changes)


class TrajectoryGit:
    """
    Git-like system for care trajectories.
    
    Operations:
    - commit(message, changes) - Record a state update
    - branch(name, description) - Fork a "what if" path
    - checkout(branch) - Switch to a branch
    - diff(from_time, to_time) - Show what changed
    - log() - Show commit history
    - merge(branch) - Adopt a branch as main path
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.commits: Dict[str, Commit] = {}
        self.branches: Dict[str, Branch] = {}
        self.state = PatientState(patient_id=patient_id)
        
        # Initialize with genesis commit
        genesis = self._create_genesis_commit()
        self.commits[genesis.commit_id] = genesis
        
        # Create main branch
        self.branches["main"] = Branch(
            name="main",
            forked_from=genesis.commit_id,
            head=genesis.commit_id,
            description="Current care trajectory",
            created_at=datetime.now().isoformat()
        )
    
    def _create_genesis_commit(self) -> Commit:
        """Create initial commit (like git init)."""
        genesis_id = self._generate_commit_id("genesis")
        return Commit(
            commit_id=genesis_id,
            timestamp=datetime.now().isoformat(),
            author="system",
            message="Initial patient state",
            state_changes={
                "status": "discharged",
                "initialized": True
            },
            parent_commit_id=None,
            branch="main"
        )
    
    def commit(self, message: str, changes: Dict[str, Any], author: str = "system") -> Commit:
        """
        Record a state update (like git commit).
        
        Example:
            git.commit(
                "Day 3: Blood pressure stable",
                {"vitals.bp": "120/80", "status": "stable"}
            )
        """
        current_branch = self.branches[self.state.current_branch]
        parent_id = current_branch.head
        
        # Generate commit ID
        commit_id = self._generate_commit_id(f"{message}{datetime.now().isoformat()}")
        
        commit = Commit(
            commit_id=commit_id,
            timestamp=datetime.now().isoformat(),
            author=author,
            message=message,
            state_changes=changes,
            parent_commit_id=parent_id,
            branch=self.state.current_branch
        )
        
        # Save commit
        self.commits[commit_id] = commit
        
        # Update branch head
        current_branch.head = commit_id
        
        # Apply changes to state
        self.state.update(changes)
        
        return commit
    
    def branch(self, name: str, description: str, probability: float = 0.5) -> Branch:
        """
        Create a new branch (alternative care path).
        
        Example:
            git.branch(
                "medication-b-pathway",
                "What if we switch to Medication B?",
                probability=0.7
            )
        """
        current_branch = self.branches[self.state.current_branch]
        fork_point = current_branch.head
        
        branch = Branch(
            name=name,
            forked_from=fork_point,
            head=fork_point,  # Starts at same commit as fork point
            description=description,
            created_at=datetime.now().isoformat(),
            probability=probability
        )
        
        self.branches[name] = branch
        return branch
    
    def checkout(self, branch_name: str):
        """
        Switch to a different branch.
        
        Example:
            git.checkout("medication-b-pathway")
        """
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' does not exist")
        
        self.state.current_branch = branch_name
        
        # Rebuild state from commit history
        self._rebuild_state_from_branch(branch_name)
    
    def diff(self, from_ref: str, to_ref: str = "HEAD") -> List[Dict]:
        """
        Show what changed between two points.
        
        Example:
            # What changed since this morning?
            git.diff("9am", "now")
            
            # What's different between branches?
            git.diff("main", "medication-b-pathway")
        """
        from_commits = self._get_commits_since(from_ref)
        
        changes = []
        for commit in from_commits:
            changes.append({
                "commit": commit.short_id(),
                "time": commit.timestamp,
                "author": commit.author,
                "message": commit.message,
                "changes": commit.state_changes
            })
        
        return changes
    
    def log(self, branch: Optional[str] = None, limit: int = 10) -> List[Commit]:
        """
        Show commit history (like git log).
        
        Example:
            commits = git.log("main", limit=5)
        """
        branch_name = branch or self.state.current_branch
        branch_obj = self.branches[branch_name]
        
        # Walk back from head
        commits = []
        current_id = branch_obj.head
        
        while current_id and len(commits) < limit:
            commit = self.commits[current_id]
            commits.append(commit)
            current_id = commit.parent_commit_id
        
        return commits
    
    def merge(self, branch_name: str, strategy: str = "adopt") -> Dict:
        """
        Merge a branch into current branch.
        
        Example:
            # Family decides to go with medication B
            git.merge("medication-b-pathway")
        """
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' does not exist")
        
        source_branch = self.branches[branch_name]
        target_branch = self.branches[self.state.current_branch]
        
        # Get commits in source branch that aren't in target
        merge_commits = self._get_unique_commits(branch_name, self.state.current_branch)
        
        # Create merge commit
        merge_commit = self.commit(
            f"Merge '{branch_name}' into {self.state.current_branch}",
            {
                "merge": True,
                "source_branch": branch_name,
                "commits_merged": len(merge_commits)
            },
            author="system"
        )
        
        return {
            "merged": True,
            "commit": merge_commit.to_dict(),
            "commits_merged": [c.to_dict() for c in merge_commits]
        }
    
    def visualize_tree(self) -> Dict[str, Any]:
        """
        Get tree structure for visualization.
        
        Returns data suitable for D3.js tree or similar.
        """
        nodes = []
        edges = []
        
        for commit_id, commit in self.commits.items():
            nodes.append({
                "id": commit.short_id(),
                "label": commit.message,
                "branch": commit.branch,
                "timestamp": commit.timestamp,
                "type": "commit"
            })
            
            if commit.parent_commit_id:
                edges.append({
                    "from": self.commits[commit.parent_commit_id].short_id(),
                    "to": commit.short_id(),
                    "branch": commit.branch
                })
        
        # Add branch nodes
        for branch_name, branch in self.branches.items():
            if branch_name != "main":
                nodes.append({
                    "id": f"branch-{branch_name}",
                    "label": branch.description,
                    "branch": branch_name,
                    "type": "branch",
                    "probability": branch.probability
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "branches": {name: b.to_dict() for name, b in self.branches.items()}
        }
    
    def _generate_commit_id(self, data: str) -> str:
        """Generate commit ID (hash of data)."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _rebuild_state_from_branch(self, branch_name: str):
        """Rebuild state by replaying commits in branch."""
        branch = self.branches[branch_name]
        commits = self.log(branch_name, limit=1000)
        
        # Reset state
        self.state.state = {}
        
        # Replay commits in order (oldest first)
        for commit in reversed(commits):
            self.state.update(commit.state_changes)
    
    def _get_commits_since(self, from_ref: str) -> List[Commit]:
        """Get commits since a reference point."""
        # Simplified - in reality would parse timestamps
        current_branch = self.branches[self.state.current_branch]
        return self.log(limit=10)  # Last 10 commits
    
    def _get_unique_commits(self, source: str, target: str) -> List[Commit]:
        """Get commits in source that aren't in target."""
        source_commits = set(c.commit_id for c in self.log(source, limit=100))
        target_commits = set(c.commit_id for c in self.log(target, limit=100))
        unique_ids = source_commits - target_commits
        return [self.commits[cid] for cid in unique_ids if cid in self.commits]


# Example usage
if __name__ == "__main__":
    git = TrajectoryGit("synthetic-001")
    
    # Simulate care trajectory
    print("=== Initial Timeline ===\n")
    
    # Day 1: Discharge
    git.commit(
        "Discharge: Medication A prescribed",
        {"medications": ["Medication A 10mg"], "status": "discharged"}
    )
    
    # Day 3: Stable
    git.commit(
        "Day 3: Vitals stable",
        {"vitals.bp": "120/80", "vitals.hr": "72", "status": "stable"}
    )
    
    # Day 5: Side effect
    git.commit(
        "Day 5: Patient reports nausea",
        {"symptoms": ["nausea"], "status": "side_effect_reported"}
    )
    
    print("Main branch commits:")
    for commit in git.log("main"):
        print(f"  {commit.short_id()} - {commit.message}")
    
    # Family asks: "What if we tried Medication B?"
    print("\n=== Creating Alternative Path ===\n")
    
    git.branch(
        "medication-b-pathway",
        "Alternative: Switch to Medication B",
        probability=0.7
    )
    
    git.checkout("medication-b-pathway")
    
    git.commit(
        "Day 5 (alt): Switch to Medication B",
        {"medications": ["Medication B 15mg"], "status": "medication_changed"}
    )
    
    git.commit(
        "Day 7 (alt): Monitor liver enzymes",
        {"labs": {"ALT": 35, "AST": 28}, "status": "monitoring"}
    )
    
    git.commit(
        "Day 10 (alt): Symptom improvement",
        {"symptoms": [], "status": "improved"}
    )
    
    print("Medication B pathway commits:")
    for commit in git.log("medication-b-pathway"):
        print(f"  {commit.short_id()} - {commit.message}")
    
    # Visualize tree
    print("\n=== Trajectory Tree ===\n")
    tree = git.visualize_tree()
    print(f"Branches: {list(tree['branches'].keys())}")
    print(f"Total commits: {len(tree['nodes'])}")
    
    # Show diff
    print("\n=== What Changed in Alt Path? ===\n")
    git.checkout("main")
    main_head = git.branches["main"].head
    alt_head = git.branches["medication-b-pathway"].head
    
    print(f"Main path current state: {git.state.state}")
    git.checkout("medication-b-pathway")
    print(f"Alt path current state: {git.state.state}")
