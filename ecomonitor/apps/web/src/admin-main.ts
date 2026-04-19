/**
 * admin-main.ts — entry point for the /admin page.
 *
 * Mounts the feedback inbox into #admin-root. Access is enforced both on the
 * server (Clerk role in publicMetadata) and here for a fast 403 before any
 * API calls land.
 */
import { initAuthState } from '@/services/auth-state';
import { mountAdminFeedbackPanel } from '@/components/AdminFeedbackPanel';

async function main() {
  const host = document.getElementById('admin-root');
  if (!host) return;

  host.textContent = 'Loading…';

  try {
    await initAuthState();
  } catch (e) {
    host.textContent = `Auth init failed: ${(e as Error).message}`;
    return;
  }

  while (host.firstChild) host.removeChild(host.firstChild);
  mountAdminFeedbackPanel(host);
}

void main();
