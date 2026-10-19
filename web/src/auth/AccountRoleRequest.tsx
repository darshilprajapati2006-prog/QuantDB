import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';
import { request } from '../lib/api';
import { useAuth } from './AuthProvider';

type RoleRequestState={requested_role:string;reason:string;status:'PENDING'|'APPROVED'|'REJECTED';created_at?:string}|null;
const choices=['QUANT_TRADER','QUANT_RESEARCHER','QUANT_DEVELOPER'];
export function AccountRoleRequest(){
 const {requestRole,profile}=useAuth();const [role,setRole]=useState(choices[0]);const [reason,setReason]=useState('');const [open,setOpen]=useState(false);const [message,setMessage]=useState('');
 const {data:existing,refetch,isError}=useQuery({queryKey:['my-role-request'],queryFn:()=>request<RoleRequestState>('/auth/role-request'),staleTime:60_000});
 const mutation=useMutation({mutationFn:()=>requestRole(role,reason),onSuccess:async()=>{setMessage('Request sent to admin.');setReason('');await refetch();},onError:(error:Error)=>setMessage(error.message.replace(/^API \\d+: /,''))});
 return <div className="role-request">{isError?<small className="role-request-message">Role requests are temporarily unavailable. Please contact the QuantDB administrator.</small>:existing?.status==='PENDING'?<div className="role-request-pending"><ShieldCheck size={15}/><span>Role request pending<br/><small>{existing.requested_role.replace(/_/g,' ')}</small></span></div>:<><button className="role-request-toggle" onClick={()=>setOpen(!open)}><ArrowUpRight size={15}/>{open?'Close role request':'Request a role upgrade'}</button>{open&&<div className="role-request-form"><label>Requested role<select value={role} onChange={e=>setRole(e.target.value)}>{choices.filter(item=>item!==profile?.role).map(item=><option value={item} key={item}>{item.replace(/_/g,' ')}</option>)}</select></label><label>Why do you need it?<textarea maxLength={500} rows={3} value={reason} onChange={e=>setReason(e.target.value)} placeholder="Briefly describe your project or access need."/></label>{message&&<small className="role-request-message">{message}</small>}<button disabled={mutation.isPending} onClick={()=>mutation.mutate()}>{mutation.isPending?'Sending…':'Send request'}</button></div>}</>}</div>;
}
