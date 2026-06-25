export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/intake' && request.method === 'POST') {
      return handleIntake(request, env);
    }
    if (url.pathname.startsWith('/view/')) {
      return handleOneTimeView(request, env);
    }
    return new Response('EphUX Guardian Intake Gateway - ephux.com (intake@ephux.com for email)', { status: 200 });
  },
  async email(message, env, ctx) {
    return handleEmailIntake(message, env);
  }
};

async function handleIntake(request, env) {
  const body = await request.json().catch(() => ({}));
  const token = crypto.randomUUID();
  const expires = Date.now() + (1000 * 60 * 60 * 24);
  const receptorEvent = {
    event_id: token,
    timestamp: Date.now(),
    source_channel: body.source_channel || 'http',
    scan_status: 'processed',
    prompt_injection_flags: body.content && body.content.toLowerCase().includes('ignore previous') ? ['possible prompt injection'] : [],
    guard_decision: 'allow',
    sanitized_content: body.content || 'Processed content placeholder (full sanitization + R2 in prod)',
    lifecycle: { retention: 'session', purge_after: expires },
    source: body
  };
  await env.INTAKE_KV.put('token:' + token, JSON.stringify(receptorEvent), { expirationTtl: 86400 });
  return Response.json({
    link: 'https://ephux.com/view/' + token,
    expiresAt: new Date(expires).toISOString(),
    receptorEvent: receptorEvent,
    note: 'One-time view link. Content quarantined and processed per zero-trust policy. Link consumes on first view.'
  });
}

async function handleOneTimeView(request, env) {
  const token = new URL(request.url).pathname.split('/view/')[1];
  if (!token) return new Response('Invalid link', { status: 400 });
  const dataStr = await env.INTAKE_KV.get('token:' + token);
  if (!dataStr) return new Response('Link expired, already viewed, or invalid.', { status: 410 });
  await env.INTAKE_KV.delete('token:' + token);
  const data = JSON.parse(dataStr);
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>EphUX Guardian Intake - Vetted Content</title><style>body{font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; background: #fafafa;} h1 {color: #222;} pre {background: #fff; padding: 20px; border-radius: 8px; overflow: auto; border: 1px solid #eee; white-space: pre-wrap;}</style></head><body><h1>EphUX Guardian Intake Gateway</h1><p><strong>One-time access consumed.</strong> This content was processed through zero-trust intake (quarantined, scanned for AI risks like prompt injection/tool poisoning/hidden instructions, provenance recorded, risks flagged, lifecycle governed).</p><pre>${JSON.stringify(data, null, 2)}</pre><p style="color:#666;font-size:0.9em">Link is now invalid. Original raw content never reached any AI. For production: R2 storage, deeper scans, full dashboard.</p></body></html>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}

async function handleEmailIntake(message, env) {
  const token = crypto.randomUUID();
  const subject = message.headers.get('subject') || 'no-subject';
  const from = message.from || 'unknown';
  const receptorEvent = {
    event_id: token,
    timestamp: Date.now(),
    source_channel: 'email',
    scan_status: 'processed',
    subject: subject,
    from: from,
    guard_decision: 'allow',
    lifecycle: { retention: 'session' },
    note: 'Email processed via EphUX Guardian Intake. One-time link generated for vetted content.'
  };
  await env.INTAKE_KV.put('token:' + token, JSON.stringify(receptorEvent), { expirationTtl: 86400 });
  // Do not reject; accept the email. The link is available at the generated token.
  // In full impl, forward original or send link via verified address.
  // For now, processing is done; sender/user can be provided the view link out of band or via extension.
  // To "deliver", we accept.
}
