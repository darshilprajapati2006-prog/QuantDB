import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, ShieldCheck, Users, RefreshCw, Save, CheckCircle2 } from 'lucide-react';
import { request } from '../lib/api';

type Account = { user_id: number; username: string; name: string; email: string; role: string; status: string; is_verified: boolean; created_at?: string };
type RoleRequestRow = { request_id: number; user_id: number; name: string; email: string; current_role: string; requested_role: string; reason: string; created_at: string };
const roles = ['USER', 'QUANT_TRADER', 'QUANT_RESEARCHER', 'QUANT_DEVELOPER', 'ADMIN'];
const roleNames: Record<string, string> = { USER: 'User', QUANT_TRADER: 'Quant Trader', QUANT_RESEARCHER: 'Quant Researcher', QUANT_DEVELOPER: 'Quant Developer', ADMIN: 'Admin' };

export function AdminPage() {
  const client = useQueryClient();
  const [search, setSearch] = useState('');
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [notice, setNotice] = useState('');
  const { data: users = [], isLoading, isError, refetch, isFetching } = useQuery({ queryKey: ['admin-users'], queryFn: () => request<Account[]>('/admin/users') });
  const { data: roleRequests = [], refetch: refetchRoleRequests, isError: roleRequestsError } = useQuery({ queryKey: ['admin-role-requests'], queryFn: () => request<RoleRequestRow[]>('/admin/role-requests') });
  const reviewRequest = useMutation({ mutationFn: ({ id, decision }: { id: number; decision: 'APPROVED'|'REJECTED' }) => request(`/admin/role-requests/${id}`, { method: 'PATCH', body: JSON.stringify({ decision }) }), onSuccess: async () => { await Promise.all([refetchRoleRequests(), client.invalidateQueries({ queryKey: ['admin-users'] })]); setNotice('Role request reviewed.'); } });
  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) => request(`/admin/users/${userId}/role`, { method: 'PATCH', body: JSON.stringify({ role }) }),
    onSuccess: () => { setNotice('Role saved. Access rules apply on the next request.'); setDrafts({}); void client.invalidateQueries({ queryKey: ['admin-users'] }); },
  });
  const filtered = useMemo(() => users.filter((user) => `${user.name} ${user.username} ${user.email}`.toLowerCase().includes(search.toLowerCase())), [users, search]);

  return <div className="space-y-6">
    <div className="page-heading"><div><div className="eyebrow"><span className="pulse"/> PLATFORM GOVERNANCE <span className="eyebrow-sep">/</span> ADMIN</div><h1>User & Role Management</h1><p>Review verified accounts and control access to QuantDB research modules.</p></div><button className="outline-button" onClick={() => { setNotice(''); void refetch(); }}><RefreshCw size={14} className={isFetching ? 'animate-spin' : ''}/> Refresh users</button></div>

    <div className="metric-grid admin-metrics"><article className="metric-card"><div className="metric-head"><span>REGISTERED ACCOUNTS</span><span className="metric-icon tone-0"><Users size={16}/></span></div><div className="metric-value">{users.length}</div><div className="metric-foot"><span>QuantDB profiles</span></div></article><article className="metric-card"><div className="metric-head"><span>EMAIL VERIFIED</span><span className="metric-icon tone-1"><CheckCircle2 size={16}/></span></div><div className="metric-value">{users.filter((user) => user.is_verified).length}</div><div className="metric-foot"><span>Verified accounts</span></div></article><article className="metric-card"><div className="metric-head"><span>PRIVILEGED ROLES</span><span className="metric-icon tone-2"><ShieldCheck size={16}/></span></div><div className="metric-value">{users.filter((user) => user.role === 'ADMIN' || user.role === 'QUANT_DEVELOPER').length}</div><div className="metric-foot"><span>Admin & developer</span></div></article><article className="metric-card"><div className="metric-head"><span>ACTIVE ACCOUNTS</span><span className="metric-icon tone-3"><Users size={16}/></span></div><div className="metric-value">{users.filter((user) => user.status === 'ACTIVE').length}</div><div className="metric-foot"><span>Currently enabled</span></div></article></div>

    <section className="panel admin-table-panel"><div className="admin-toolbar"><div className="relative"><Search size={15}/><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name, username, or email"/></div><span>{filtered.length} accounts</span></div>
      {(notice || (updateRole.error instanceof Error ? updateRole.error.message : '')) && <div className={`api-note ${updateRole.error ? 'error' : ''}`}>{updateRole.error instanceof Error ? updateRole.error.message : notice}</div>}
      {isLoading ? <div className="empty-panel-state">Loading verified user profiles…</div> : isError ? <div className="empty-panel-state">Could not load users. Check the API and database, then refresh.</div> : <div className="admin-table-scroll"><table className="admin-table"><thead><tr><th>USER</th><th>EMAIL</th><th>ROLE</th><th>STATUS</th><th>EMAIL VERIFIED</th><th>CREATED</th><th/></tr></thead><tbody>{filtered.map((user) => {
        const draft = drafts[user.user_id] ?? user.role;
        const changed = draft !== user.role;
        return <tr key={user.user_id}><td><div className="admin-user"><span>{(user.name || user.username || 'Q').slice(0, 2).toUpperCase()}</span><div><b>{user.name || user.username}</b><small>@{user.username}</small></div></div></td><td className="admin-email">{user.email}</td><td><select aria-label={`Role for ${user.email}`} value={draft} onChange={(event) => setDrafts((current) => ({ ...current, [user.user_id]: event.target.value }))}>{roles.map((role) => <option key={role} value={role}>{roleNames[role]}</option>)}</select></td><td><span className={`admin-status ${user.status === 'ACTIVE' ? 'active' : 'inactive'}`}>{user.status || 'UNKNOWN'}</span></td><td><span className={`verified-state ${user.is_verified ? 'verified' : 'unverified'}`}>{user.is_verified ? 'Verified' : 'Pending'}</span></td><td className="admin-date">{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td><td>{changed && <button className="admin-save" disabled={updateRole.isPending} onClick={() => { setNotice(''); updateRole.mutate({ userId: user.user_id, role: draft }); }}><Save size={13}/> Save</button>}</td></tr>;
      })}</tbody></table>{filtered.length === 0 && <div className="empty-panel-state">No account matches this search.</div>}</div>}
    </section>
    <section className="panel admin-table-panel"><div className="admin-toolbar"><b>Pending role requests</b><span>{roleRequestsError?'Unavailable':`${roleRequests.length} awaiting review`}</span></div>{roleRequestsError?<div className="empty-panel-state">The request queue is unavailable. Check the API and role-request database setup.</div>:roleRequests.length===0?<div className="empty-panel-state">No role requests are pending.</div>:<div className="role-requests-list">{roleRequests.map(item=><article className="role-request-row" key={item.request_id}><div><b>{item.name} · {item.email}</b><small>{item.current_role} → {item.requested_role.replace(/_/g,' ')}{item.reason?` · ${item.reason}`:''}</small></div><div><button className="admin-save" disabled={reviewRequest.isPending} onClick={()=>reviewRequest.mutate({id:item.request_id,decision:'APPROVED'})}>Approve</button><button className="admin-reject" disabled={reviewRequest.isPending} onClick={()=>reviewRequest.mutate({id:item.request_id,decision:'REJECTED'})}>Reject</button></div></article>)}</div>}</section>
    <div className="admin-security-note"><ShieldCheck size={16}/><span>New verified sign-ups receive the User role. Role upgrades require admin review and API-side approval.</span></div>
  </div>;
}
