import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';
import { request } from '../lib/api';
import { useAuth } from './AuthProvider';

type RoleRequestState = { requested_role: string; reason: string; status: 'PENDING' | 'APPROVED' | 'REJECTED'; created_at?: string } | null;
const choices = ['USER', 'QUANT_TRADER', 'QUANT_RESEARCHER', 'QUANT_DEVELOPER'];

export function AccountRoleRequest() {
  const { requestRole, profile, refreshProfile } = useAuth();
  const [role, setRole] = useState(choices[0]);
  const [reason, setReason] = useState('');
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const { data: existing, refetch, isError } = useQuery<RoleRequestState>({
    queryKey: ['my-role-request', profile?.user_id],
    queryFn: () => request<RoleRequestState>('/auth/role-request'),
    enabled: Boolean(profile?.user_id),
    refetchInterval: 15000,
    retry: false,
  });
  const refreshedRequest = useRef<number | null>(null);
  useEffect(() => {
    if (existing?.status === 'APPROVED' && refreshedRequest.current !== profile?.user_id) {
      refreshedRequest.current = profile?.user_id ?? null;
      void refreshProfile();
    }
  }, [existing?.status, profile?.user_id, refreshProfile]);
  const mutation = useMutation({
    mutationFn: () => requestRole(selectedRole, reason),
    onSuccess: async () => { setMessage('Request sent to admin.'); setReason(''); await refetch(); },
    onError: (error: Error) => setMessage(error.message.replace(/^API \d+: /, '')),
  });
  const availableRoles = choices.filter((item) => item !== profile?.role);
  const selectedRole = availableRoles.includes(role) ? role : availableRoles[0] || '';

  return (
    <div className="role-request">
      {existing?.status === 'PENDING' ? (
        <div className="role-request-pending"><ShieldCheck size={15}/><span>Role request pending<br/><small>{existing.requested_role.replace(/_/g, ' ')}</small></span></div>
      ) : (
        <>
          {existing?.status === 'APPROVED' && <div className="role-request-result approved"><ShieldCheck size={14}/> Approved · your access is updated</div>}
          {existing?.status === 'REJECTED' && <div className="role-request-result rejected">Previous request declined · you can submit another</div>}
          <button className="role-request-toggle" onClick={() => setOpen(!open)}><ArrowUpRight size={15}/>{open ? 'Close role request' : 'Request a role change'}</button>
          {isError && <small className="role-request-message">Could not load request status. You can still submit a request or <button className="role-request-retry" onClick={() => void refetch()}>retry</button>.</small>}
          {open && <div className="role-request-form">
            <label>Requested role<select required value={selectedRole} onChange={(event) => setRole(event.target.value)}>{availableRoles.map((item) => <option value={item} key={item}>{item.replace(/_/g, ' ')}</option>)}</select></label>
            <label>Why do you need it?<textarea maxLength={500} rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Briefly describe your project or access need."/></label>
            {message && <small className="role-request-message">{message}</small>}
            <button disabled={mutation.isPending || !selectedRole} onClick={() => mutation.mutate()}>{mutation.isPending ? 'Sending…' : 'Send request'}</button>
          </div>}
        </>
      )}
    </div>
  );
}
