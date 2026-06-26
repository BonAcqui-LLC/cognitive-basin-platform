# Owner Review Flow

This note is for maintainers who want a simple, low-stress way to review community activity.

## What Happens When Someone Forks

The repository includes a GitHub Actions workflow at `.github/workflows/fork-notice.yml`.

When someone forks the repository, the workflow should create an issue in the main repository titled:

`Fork notice: owner/repo`

That gives maintainers a visible review queue inside the repo itself.

## Why This Helps

GitHub's normal watch settings are built around repository activity such as issues, pull requests, releases, security alerts, and discussions. They are not designed as a direct "email me whenever someone forks" owner workflow.

By turning a fork into an issue:

- the event becomes visible in the repo,
- maintainers can comment on it together,
- and normal issue notifications can carry the alert.

## Recommended GitHub Settings

For the repository owner account:

1. Watch the repository.
2. In repository watch settings, make sure issues and pull requests are included.
3. In account notification settings, enable email and/or on-GitHub notifications for watching activity.

That way, when the workflow opens a `fork-notice` issue, it should surface through the normal notification path.

## What To Review Together

When a fork notice appears, the first questions are:

- Is this just a passive fork, or did the person also open an issue or pull request?
- Is there a part of the docs they may be trying to improve or understand?
- Should we invite them toward the atlas, whitepaper, or evidence-library lane?
- Is there a missing contribution guideline that would make the next fork easier to handle?
