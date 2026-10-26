import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Clock3, MailPlus, RefreshCw, Search, ShieldCheck, Users, X } from 'lucide-react';
import { request } from '../lib/api';

type Account = { user_id: number; username: string; name: string; email: string; role: string; status: string; is_verified: boolean; created_at?: string };
type RoleRequestRow = { request_id: number; user_id: number; name: string; email: string; current_role: string; requested_role: string; reason: string; created_at: string };
type Invitation = { invitation_id: number; email: string; name: string; role: string; created_at: string; expires_at: string };
const roles = ['USER', 'QUANT_TRADER', 'QUANT_RESEARCHER', 'QUANT_DEVELOPER'];
const roleNames: Record<string, string> = { USER: 'User', QUANT_TRADER: 'Quant Trader', QUANT_RESEARCHER: 'Quant Researcher', QUANT_DEVELOPER: 'Quant Developer', ADMIN: 'Admin' };
const roleLabel = (role: string) => roleNames[role] || role.replace(/_/g, ' ');

export function AdminPage() {
  const client = useQueryClient();
  const [search, setSearch] = useState('');
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [notice, setNotice] = useState('');
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [inviteRole, setInviteRole] = useState('USER');
  const { data: users = [], isLoading, isError, refetch, isFetching } = useQuery({ queryKey: ['admin-users'], queryFn: () => request<Account[]>('/admin/users') });
  const { data: roleRequests = [], isError: roleRequestsError } = useQuery({ queryKey: ['admin-role-requests'], queryFn: () => request<RoleRequestRow[]>('/admin/role-requests'), refetchInterval: 15000 });
  const { data: invitations = [], isError: invitationsError } = useQuery({ queryKey: ['admin-invitations'], queryFn: () => request<Invitation[]>('/admin/invitations'), refetchInterval: 15000 });
  const refreshAll = async () => Promise.all([refetch(), client.invalidateQueries({ queryKey: ['admin-role-requests'] }), client.invalidateQueries({ queryKey: ['admin-invitations'] })]);
  const reviewRequest = useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: 'APPROVED' | 'REJECTED' }) => request(`/admin/role-requests/${id}`, { method: 'PATCH', body: JSON.stringify({ decision }) }),
    onSuccess: async (_, variables) => { await refreshAll(); setNotice(`Role request ${variables.decision.toLowerCase()}.`); },
  });
  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) => request(`/admin/users/${userId}/role`, { method: 'PATCH', body: JSON.stringify({ role }) }),
    onSuccess: () => { setNotice('Role saved. Access rules apply on the next request.'); setDrafts({}); void client.invalidateQueries({ queryKey: ['admin-users'] }); },
  });
  const createInvitation = useMutation({
    mutationFn: () => request('/admin/invitations', { method: 'POST', body: JSON.stringify({ email: inviteEmail, name: inviteName, role: inviteRole }) }),
    onSuccess: async () => { setInviteEmail(''); setInviteName(''); setInviteRole('USER'); setInviteOpen(false); setNotice('Invitation saved. The invitee can create an account with this email.'); await client.invalidateQueries({ queryKey: ['admin-invitations'] }); },
  });
  const cancelInvitation = useMutation({
    mutationFn: (id: number) => request(`/admin/invitations/${id}`, { method: 'DELETE' }),
    onSuccess: async () => { setNotice('Invitation revoked.'); await client.invalidateQueries({ queryKey: ['admin-invitations'] }); },
  });
  const filtered = useMemo(() => users.filter((user) => `${user?.name || ''} ${user?.username || ''} ${user?.email || ''}`.toLowerCase().includes(search.toLowerCase())), [users, search]);
  const actionError = [updateRole.error, reviewRequest.error, createInvitation.error, cancelInvitation.error].find((error) => error instanceof Error) as Error | undefined;

  return <div className="space-y-6">
    <div className="page-heading"><div><div className="eyebrow"><span className="pulse"/> PLATFORM GOVERNANCE <span className="eyebrow-sep">/</span> ADMIN</div><h1>User & Role Management</h1><p>Review account access, invitations, and role requests in one place.</p></div><button className="outline-button" onClick={() => { setNotice(''); void refreshAll(); }}><RefreshCw size={14} className={isFetching ? 'animate-spin' : ''}/> Refresh</button></div>

    <div className="metric-grid admin-metrics admin-queue-metrics">
      <article className="metric-card"><div className="metric-head"><span>REGISTERED ACCOUNTS</span><span className="metric-icon tone-0"><Users size={16}/></span></div><div className="metric-value">{users.length}</div><div className="metric-foot"><span>QuantDB profiles</span></div></article>
      <article className="metric-card"><div className="metric-head"><span>PENDING INVITATIONS</span><span className="metric-icon tone-1"><MailPlus size={16}/></span></div><div className="metric-value">{invitationsError ? '—' : invitations.length}</div><div className="metric-foot"><span>Awaiting verified sign-up</span></div></article>
      <article className="metric-card"><div className="metric-head"><span>ROLE CHANGE REQUESTS</span><span className="metric-icon tone-2"><ShieldCheck size={16}/></span></div><div className="metric-value">{roleRequestsError ? '—' : roleRequests.length}</div><div className="metric-foot"><span>Awaiting admin review</span></div></article>
    </div>

    {(notice || actionError) && <div className={`api-note ${actionError ? 'error' : ''}`}>{actionError ? actionError.message.replace(/^API \d+: /, '') : notice}</div>}

    <section className="panel admin-table-panel">
      <div className="admin-toolbar"><div className="relative"><Search size={15}/><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name, username, or email"/></div><button className="admin-invite-trigger" onClick={() => { setInviteOpen((open) => !open); createInvitation.reset(); }}>{inviteOpen ? <X size={14}/> : <MailPlus size={14}/>} {inviteOpen ? 'Close' : 'Invite account'}</button><span>{filtered.length} accounts</span></div>
      {inviteOpen && <form className="admin-invite-form" onSubmit={(event) => { event.preventDefault(); createInvitation.mutate(); }}><label>Name (optional)<input value={inviteName} onChange={(event) => setInviteName(event.target.value)} maxLength={100} placeholder="Invitee name"/></label><label>Email address<input type="email" required value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="name@institution.edu"/></label><label>Assigned role<select value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>{roles.map((role) => <option key={role} value={role}>{roleLabel(role)}</option>)}</select></label><button className="admin-save" disabled={createInvitation.isPending}>{createInvitation.isPending ? 'Saving…' : 'Create invitation'}</button><small>Role is assigned after the invitee signs up and verifies this email. Invitations expire in 7 days.</small></form>}
      {isLoading ? <div className="empty-panel-state">Loading user profiles…</div> : isError ? <div className="empty-panel-state">Could not load users. Check the API and database, then refresh.</div> : <div className="admin-table-scroll"><table className="admin-table"><thead><tr><th>USER</th><th>EMAIL</th><th>ROLE</th><th>STATUS</th><th>EMAIL VERIFIED</th><th>CREATED</th><th/></tr></thead><tbody>{filtered.map((user) => {
        const draft = drafts[user.user_id] ?? user.role;
        const changed = draft !== user.role;
        return <tr key={user.user_id}><td><div className="admin-user"><span>{(user.name || user.username || 'Q').slice(0, 2).toUpperCase()}</span><div><b>{user.name || user.username}</b><small>@{user.username}</small></div></div></td><td className="admin-email">{user.email}</td><td><select aria-label={`Role for ${user.email}`} value={draft} onChange={(event) => setDrafts((current) => ({ ...current, [user.user_id]: event.target.value }))}>{[...roles, ...(user.role === 'ADMIN' ? ['ADMIN'] : [])].map((role) => <option key={role} value={role}>{roleLabel(role)}</option>)}</select></td><td><span className={`admin-status ${user.status === 'ACTIVE' ? 'active' : 'inactive'}`}>{user.status || 'UNKNOWN'}</span></td><td><span className={`verified-state ${user.is_verified ? 'verified' : 'unverified'}`}>{user.is_verified ? 'Verified' : 'Pending'}</span></td><td className="admin-date">{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td><td>{changed && <button className="admin-save" disabled={updateRole.isPending} onClick={() => updateRole.mutate({ userId: user.user_id, role: draft })}>Save role</button>}</td></tr>;
      })}</tbody></table>{filtered.length === 0 && <div className="empty-panel-state">No account matches this search.</div>}</div>}
    </section>

    <section className="panel admin-table-panel"><div className="admin-toolbar"><div className="admin-section-title"><ShieldCheck size={16}/><b>Role change requests</b></div><span>{roleRequestsError ? 'Unavailable' : `${roleRequests.length} awaiting review`}</span></div>{roleRequestsError ? <div className="empty-panel-state">Request queue unavailable. Check the role request database migration and API.</div> : roleRequests.length === 0 ? <div className="empty-panel-state">No role requests are pending.</div> : <div className="role-requests-list">{roleRequests.map((item) => <article className="role-request-row" key={item.request_id}><div><b>{item.name || item.email}</b><small>{item.email} <span className="request-role-change">{roleLabel(item.current_role)} → {roleLabel(item.requested_role)}</span></small>{item.reason && <p>{item.reason}</p>}</div><div className="role-request-actions"><button className="admin-save" disabled={reviewRequest.isPending} onClick={() => reviewRequest.mutate({ id: item.request_id, decision: 'APPROVED' })}><CheckCircle2 size={13}/> Approve</button><button className="admin-reject" disabled={reviewRequest.isPending} onClick={() => reviewRequest.mutate({ id: item.request_id, decision: 'REJECTED' })}>Reject</button></div></article>)}</div>}</section>

    <section className="panel admin-table-panel"><div className="admin-toolbar"><div className="admin-section-title"><Clock3 size={16}/><b>Pending invitations</b></div><span>{invitationsError ? 'Unavailable' : `${invitations.length} awaiting sign-up`}</span></div>{invitationsError ? <div className="empty-panel-state">Invitation queue unavailable. Check the database migration and API.</div> : invitations.length === 0 ? <div className="empty-panel-state">No invitations are waiting for sign-up.</div> : <div className="role-requests-list">{invitations.map((item) => <article className="role-request-row" key={item.invitation_id}><div><b>{item.name || item.email}</b><small>{item.email} <span className="request-role-change">{roleLabel(item.role)}</span> · Expires {new Date(item.expires_at).toLocaleDateString()}</small></div><button className="admin-reject" disabled={cancelInvitation.isPending} onClick={() => cancelInvitation.mutate(item.invitation_id)}>Revoke</button></article>)}</div>}</section>
    <div className="admin-security-note"><ShieldCheck size={16}/><span>New sign-ups receive User access unless a verified email matches an active invitation. Role upgrades take effect after admin approval.</span></div>
  </div>;
}
