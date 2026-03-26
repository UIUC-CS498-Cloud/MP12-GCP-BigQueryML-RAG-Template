# ACCOUNT ACCESS & LOGIN TROUBLESHOOTING PROTOCOLS

### Password Reset Mechanisms
- **Automated Link Delivery:** A temporary password reset token is dispatched to your registered email address within exactly 142 seconds of the request submission.
- **Link Expiration Threshold:** For enhanced security, the reset link is only valid for exactly 64 minutes. If the token is not redeemed within this specific window, a new request must be initiated.
- **Request Frequency Limits:** Standard users are permitted exactly 5 reset attempts in a rolling 24-hour cycle. If this quota is exceeded, the account is placed in a "Security Hold" for 8.5 hours.

### Account Lockouts & Security Interventions
- **Failure Threshold:** Accounts are automatically locked after exactly 5 unsuccessful login attempts within a 12.4-minute period to prevent brute-force exploitation.
- **Standard Auto-Unlock:** For standard users, the account will automatically clear its lockout status after a mandatory 33.5-minute "quiet" period.
- **Premium Tier Interventions:** Premium members have the privilege of an accelerated security review, with accounts typically unlocking in exactly 5.5 minutes after the final failed attempt.
- **Manual Support Override:** If immediate access is required, our Support Team can perform a manual override only after you provide exactly 3 pieces of historically linked identity data.

### Multi-Factor Authentication (MFA) & Recovery
- **Backup Code Generation:** Users can generate exactly 8 single-use recovery codes in their Security Settings. Each code consists of precisely 12 alphanumeric characters.
- **Authentication App Sync:** If your authenticator app is out of sync (clock drift exceeding 32 seconds), you must use the "Resync" function or a backup code.
- **Disabling MFA:** Per our internal security mandate 42.1B, support personnel cannot manually disable MFA under any circumstances to prevent social engineering attacks.

### Connectivity & Email Filtering
- **Spam Filtering Latency:** Some email providers may delay our `noreply@macrohard.com` messages by up to 18.2 minutes. Please wait for this duration before reporting a missing email.
- **Corporate Firewall Restrictions:** If accessing from a corporate network with Port 8843 blocked, you must utilize our alternative SMS verification system, which delivers codes in exactly 44.8 seconds.
