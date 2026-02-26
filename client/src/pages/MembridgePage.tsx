import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  FolderOpen,
  Crown,
  Server,
  RefreshCw,
  Shield,
  Hash,
  Network,
  AlertCircle,
  GitBranch,
  Plus,
  Copy,
  Trash2,
  Database,
  Loader2,
} from "lucide-react";

interface MembridgeProject {
  name: string;
  canonical_id: string;
  path?: string;
  source?: string;
}

interface ManagedProject {
  id: string;
  name: string;
  repo_url: string;
  canonical_id: string;
  target_path: string | null;
  clone_status: string;
  primary_node_id: string | null;
  created_at: number;
  updated_at: number;
  error_message: string | null;
}

interface ProjectNodeCloneStatus {
  id: string;
  project_id: string;
  node_id: string;
  clone_status: string;
  last_sync_at: number | null;
  error_message: string | null;
  repo_path: string | null;
}

interface LeadershipLease {
  canonical_id: string;
  primary_node_id: string;
  issued_at: number;
  expires_at: number;
  lease_seconds: number;
  epoch: number;
  policy: string;
  issued_by: string;
  needs_ui_selection: boolean;
}

interface ProjectNode {
  node_id: string;
  role: string;
  obs_count: number;
  db_sha: string;
  last_seen: number;
  ip_addrs: string[];
}

function formatRelative(ts: number | null) {
  if (!ts) return "—";
  const now = Date.now();
  const tsMs = ts < 1e12 ? ts * 1000 : ts;
  const diff = now - tsMs;
  if (diff < 0) return "in the future";
  if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
  return `${Math.round(diff / 3600000)}h ago`;
}

function formatTime(ts: number | null) {
  if (!ts) return "—";
  const tsMs = ts < 1e12 ? ts * 1000 : ts;
  return new Date(tsMs).toLocaleString();
}

function roleBadge(role: string) {
  if (role === "primary") {
    return <Badge data-testid={`badge-role-${role}`} variant="default">{role}</Badge>;
  }
  return <Badge data-testid={`badge-role-${role}`} variant="secondary">{role}</Badge>;
}

function cloneStatusBadge(status: string) {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    synced: "default",
    cloned: "default",
    cloning: "secondary",
    propagating: "secondary",
    pending: "outline",
    failed: "destructive",
  };
  return <Badge data-testid={`badge-clone-${status}`} variant={variants[status] || "outline"}>{status}</Badge>;
}

function AddProjectForm() {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [targetPath, setTargetPath] = useState("");
  const [primaryNode, setPrimaryNode] = useState("");

  const createMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, any> = { name, repo_url: repoUrl };
      if (targetPath.trim()) body.target_path = targetPath.trim();
      if (primaryNode.trim()) body.primary_node_id = primaryNode.trim();
      const res = await apiRequest("POST", "/api/runtime/projects", body);
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      toast({ title: "Project created", description: `"${data.name}" added. Now clone it to a node.` });
      setName("");
      setRepoUrl("");
      setTargetPath("");
      setPrimaryNode("");
    },
    onError: (err: Error) => {
      toast({ title: "Failed to create project", description: err.message, variant: "destructive" });
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Plus className="h-4 w-4" />
          Add Project
        </CardTitle>
        <CardDescription>
          Add a git repository to clone and sync across all nodes.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 max-w-lg">
          <div className="space-y-2">
            <Label htmlFor="add-project-name">Project Name</Label>
            <Input
              id="add-project-name"
              data-testid="input-project-name"
              placeholder="e.g. membridge"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-repo-url">Repository URL</Label>
            <Input
              id="add-repo-url"
              data-testid="input-repo-url"
              placeholder="https://github.com/user/repo.git"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-target-path">Target Path (optional)</Label>
            <Input
              id="add-target-path"
              data-testid="input-target-path"
              placeholder="e.g. ~/projects/membridge"
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-primary-node">Primary Node (optional)</Label>
            <Input
              id="add-primary-node"
              data-testid="input-primary-node"
              placeholder="e.g. rpi4b"
              value={primaryNode}
              onChange={(e) => setPrimaryNode(e.target.value)}
            />
          </div>
          <Button
            data-testid="button-create-project"
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending || !name.trim() || !repoUrl.trim()}
          >
            {createMutation.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Creating...</>
            ) : (
              <><GitBranch className="h-4 w-4 mr-2" />Add Project</>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ManagedProjectCard({
  project,
  onSelect,
}: {
  project: ManagedProject;
  onSelect: () => void;
}) {
  const { toast } = useToast();

  const cloneMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", `/api/runtime/projects/${project.id}/clone`, {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      toast({ title: "Clone started", description: `Cloning "${project.name}" on primary node.` });
    },
    onError: (err: Error) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      toast({ title: "Clone failed", description: err.message, variant: "destructive" });
    },
  });

  const propagateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", `/api/runtime/projects/${project.id}/propagate`, {});
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      const count = data.results?.filter((r: any) => r.status === "cloned").length || 0;
      toast({ title: "Propagation complete", description: `Cloned to ${count} additional node(s).` });
    },
    onError: (err: Error) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      toast({ title: "Propagation failed", description: err.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("DELETE", `/api/runtime/projects/${project.id}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects"] });
      toast({ title: "Project removed", description: `"${project.name}" deleted.` });
    },
    onError: (err: Error) => {
      toast({ title: "Delete failed", description: err.message, variant: "destructive" });
    },
  });

  const isCloned = project.clone_status === "cloned" || project.clone_status === "synced";
  const isBusy = cloneMutation.isPending || propagateMutation.isPending || deleteMutation.isPending;

  return (
    <Card data-testid={`card-managed-project-${project.id}`}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0 cursor-pointer" onClick={onSelect}>
            <div className="flex items-center gap-2 mb-1">
              <GitBranch className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="font-medium text-sm truncate" data-testid={`text-project-name-${project.id}`}>
                {project.name}
              </span>
              {cloneStatusBadge(project.clone_status)}
            </div>
            <div className="text-xs text-muted-foreground font-mono truncate" data-testid={`text-repo-url-${project.id}`}>
              {project.repo_url}
            </div>
            <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
              <span>CID: {project.canonical_id}</span>
              {project.primary_node_id && <span>Primary: {project.primary_node_id}</span>}
              <span>{formatRelative(project.created_at)}</span>
            </div>
            {project.error_message && (
              <div className="flex items-center gap-1 mt-1 text-xs text-destructive">
                <AlertCircle className="h-3 w-3" />
                {project.error_message}
              </div>
            )}
          </div>
          <div className="flex gap-1 flex-shrink-0">
            {!isCloned && (
              <Button
                data-testid={`button-clone-${project.id}`}
                variant="outline"
                size="sm"
                disabled={isBusy || !project.primary_node_id}
                onClick={() => cloneMutation.mutate()}
                title={!project.primary_node_id ? "Set a primary node first" : "Clone to primary node"}
              >
                {cloneMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Copy className="h-3 w-3" />}
              </Button>
            )}
            {isCloned && (
              <Button
                data-testid={`button-propagate-${project.id}`}
                variant="outline"
                size="sm"
                disabled={isBusy}
                onClick={() => propagateMutation.mutate()}
                title="Propagate to all other nodes"
              >
                {propagateMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Network className="h-3 w-3" />}
              </Button>
            )}
            <Button
              data-testid={`button-delete-${project.id}`}
              variant="ghost"
              size="sm"
              disabled={isBusy}
              onClick={() => deleteMutation.mutate()}
            >
              <Trash2 className="h-3 w-3 text-destructive" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ManagedProjectDetail({ project }: { project: ManagedProject }) {
  const { toast } = useToast();

  const nodeStatusQuery = useQuery<ProjectNodeCloneStatus[]>({
    queryKey: ["/api/runtime/projects", project.id, "node-status"],
    refetchInterval: 10000,
  });

  const syncMutation = useMutation({
    mutationFn: async (direction: string) => {
      const res = await apiRequest("POST", `/api/runtime/projects/${project.id}/sync-memory`, { direction });
      return res.json();
    },
    onSuccess: (data) => {
      toast({ title: "Memory sync", description: `${data.direction} completed via ${data.node}` });
    },
    onError: (err: Error) => {
      toast({ title: "Sync failed", description: err.message, variant: "destructive" });
    },
  });

  const nodeStatuses = nodeStatusQuery.data || [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Database className="h-4 w-4" />
            Project Details: {project.name}
          </CardTitle>
          <CardDescription>
            {project.repo_url}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Status</div>
              <div data-testid="text-detail-status">{cloneStatusBadge(project.clone_status)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Canonical ID</div>
              <div className="font-mono text-xs" data-testid="text-detail-cid">{project.canonical_id}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Primary Node</div>
              <div className="text-sm" data-testid="text-detail-primary">{project.primary_node_id || "—"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Created</div>
              <div className="text-sm">{formatTime(project.created_at)}</div>
            </div>
          </div>
          {project.primary_node_id && (project.clone_status === "cloned" || project.clone_status === "synced") && (
            <div className="flex gap-2 mt-4">
              <Button
                data-testid="button-memory-push"
                variant="outline"
                size="sm"
                disabled={syncMutation.isPending}
                onClick={() => syncMutation.mutate("push")}
              >
                {syncMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : null}
                Push Memory
              </Button>
              <Button
                data-testid="button-memory-pull"
                variant="outline"
                size="sm"
                disabled={syncMutation.isPending}
                onClick={() => syncMutation.mutate("pull")}
              >
                {syncMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : null}
                Pull Memory
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Server className="h-4 w-4" />
              Node Clone Status
            </CardTitle>
            <Button
              data-testid="button-refresh-node-status"
              variant="ghost"
              size="sm"
              onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/runtime/projects", project.id, "node-status"] })}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription>{nodeStatuses.length} node(s) tracked</CardDescription>
        </CardHeader>
        <CardContent>
          {nodeStatusQuery.isLoading ? (
            <div className="text-sm text-muted-foreground py-4">Loading...</div>
          ) : nodeStatuses.length === 0 ? (
            <div className="text-sm text-muted-foreground py-4" data-testid="text-no-node-status">
              No nodes have been cloned yet. Use Clone or Propagate.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Node</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Path</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {nodeStatuses.map((ns) => (
                  <TableRow key={ns.id} data-testid={`row-node-clone-${ns.node_id}`}>
                    <TableCell className="font-medium">{ns.node_id}</TableCell>
                    <TableCell>{cloneStatusBadge(ns.clone_status)}</TableCell>
                    <TableCell className="font-mono text-xs">{ns.repo_path || "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{formatRelative(ns.last_sync_at)}</TableCell>
                    <TableCell>
                      {ns.error_message ? (
                        <span className="text-xs text-destructive">{ns.error_message}</span>
                      ) : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProjectList({
  projects,
  isLoading,
  selectedCid,
  onSelect,
}: {
  projects: MembridgeProject[];
  isLoading: boolean;
  selectedCid: string | null;
  onSelect: (cid: string) => void;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <FolderOpen className="h-4 w-4" />
            Membridge Projects
          </CardTitle>
          <Button
            data-testid="button-refresh-projects"
            variant="ghost"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/membridge/projects"] })}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>{projects.length} project(s)</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="text-sm text-muted-foreground px-6 py-4" data-testid="text-projects-loading">
            Loading projects...
          </div>
        ) : projects.length === 0 ? (
          <div className="text-sm text-muted-foreground px-6 py-4" data-testid="text-projects-empty">
            No projects found. Start a membridge-agent with a registered project.
          </div>
        ) : (
          <div className="divide-y">
            {projects.map((p) => (
              <button
                key={p.canonical_id}
                data-testid={`button-project-${p.canonical_id}`}
                className={`w-full text-left px-6 py-3 hover:bg-muted/50 transition-colors ${
                  selectedCid === p.canonical_id ? "bg-muted border-l-2 border-primary" : ""
                }`}
                onClick={() => onSelect(p.canonical_id)}
              >
                <div className="font-medium text-sm">{p.name}</div>
                <div className="text-xs text-muted-foreground font-mono mt-0.5">
                  {p.canonical_id}
                </div>
                {p.source && (
                  <Badge variant="outline" className="mt-1 text-xs">
                    {p.source}
                  </Badge>
                )}
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function LeadershipCard({
  cid,
  leadership,
  isLoading,
}: {
  cid: string;
  leadership: LeadershipLease | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="text-sm text-muted-foreground">Loading leadership...</div>
        </CardContent>
      </Card>
    );
  }

  if (!leadership) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Crown className="h-4 w-4" />
            Leadership
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-muted-foreground" data-testid="text-no-leadership">
            <AlertCircle className="h-4 w-4" />
            No leadership lease found for this project.
          </div>
        </CardContent>
      </Card>
    );
  }

  const isExpired = leadership.expires_at < (Date.now() / 1000);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Crown className="h-4 w-4" />
          Leadership
        </CardTitle>
        <CardDescription>Primary/secondary model for {cid.substring(0, 8)}...</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <div className="text-xs text-muted-foreground mb-1">Primary Node</div>
            <div className="font-medium text-sm flex items-center gap-1" data-testid="text-primary-node">
              <Shield className="h-3 w-3" />
              {leadership.primary_node_id}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Canonical ID</div>
            <div className="font-mono text-xs" data-testid="text-canonical-id">
              {leadership.canonical_id}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Epoch</div>
            <div className="font-medium text-sm flex items-center gap-1" data-testid="text-epoch">
              <Hash className="h-3 w-3" />
              {leadership.epoch}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Issued</div>
            <div className="text-sm" data-testid="text-issued-at">{formatTime(leadership.issued_at)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Expires</div>
            <div className="text-sm" data-testid="text-expires-at">
              {formatTime(leadership.expires_at)}
              {isExpired && (
                <Badge variant="destructive" className="ml-2 text-xs">expired</Badge>
              )}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Status</div>
            <div data-testid="text-leadership-status">
              {leadership.needs_ui_selection ? (
                <Badge variant="destructive">needs selection</Badge>
              ) : (
                <Badge variant="default">active</Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function NodesTable({
  cid,
  nodes,
  isLoading,
}: {
  cid: string;
  nodes: ProjectNode[];
  isLoading: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Server className="h-4 w-4" />
            Nodes
          </CardTitle>
          <Button
            data-testid="button-refresh-nodes"
            variant="ghost"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/membridge/projects", cid, "nodes"] })}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>{nodes.length} node(s) registered</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground py-4">Loading nodes...</div>
        ) : nodes.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4" data-testid="text-nodes-empty">
            No nodes registered for this project.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Node ID</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Observations</TableHead>
                <TableHead>DB SHA</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>IP Addresses</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {nodes.map((n) => (
                <TableRow key={n.node_id} data-testid={`row-node-${n.node_id}`}>
                  <TableCell className="font-medium">{n.node_id}</TableCell>
                  <TableCell>{roleBadge(n.role)}</TableCell>
                  <TableCell data-testid={`text-obs-${n.node_id}`}>{n.obs_count}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {n.db_sha ? n.db_sha.substring(0, 12) + "..." : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelative(n.last_seen)}
                  </TableCell>
                  <TableCell>
                    {n.ip_addrs && n.ip_addrs.length > 0 ? (
                      <div className="flex gap-1 flex-wrap">
                        {n.ip_addrs.map((ip) => (
                          <Badge key={ip} variant="outline" className="text-xs font-mono">
                            {ip}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function PromotePrimaryForm({ cid }: { cid: string }) {
  const { toast } = useToast();
  const [nodeId, setNodeId] = useState("");
  const [leaseSeconds, setLeaseSeconds] = useState("3600");

  const promoteMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, any> = { primary_node_id: nodeId };
      const ls = parseInt(leaseSeconds);
      if (ls > 0) body.lease_seconds = ls;
      const res = await apiRequest("POST", `/api/membridge/projects/${cid}/leadership/select`, body);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/membridge/projects", cid, "leadership"] });
      queryClient.invalidateQueries({ queryKey: ["/api/membridge/projects", cid, "nodes"] });
      toast({ title: "Primary promoted", description: `${nodeId} is now the primary node.` });
      setNodeId("");
    },
    onError: (err: Error) => {
      toast({ title: "Promotion failed", description: err.message, variant: "destructive" });
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Network className="h-4 w-4" />
          Promote Primary
        </CardTitle>
        <CardDescription>
          Select a node to become the primary for this execution context.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 max-w-md">
          <div className="space-y-2">
            <Label htmlFor="promote-node-id">Node ID</Label>
            <Input
              id="promote-node-id"
              data-testid="input-promote-node-id"
              placeholder="e.g. rpi4b"
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="promote-lease-seconds">Lease Duration (seconds)</Label>
            <Input
              id="promote-lease-seconds"
              data-testid="input-promote-lease-seconds"
              type="number"
              placeholder="3600"
              value={leaseSeconds}
              onChange={(e) => setLeaseSeconds(e.target.value)}
            />
          </div>
          <Button
            data-testid="button-promote-primary"
            onClick={() => promoteMutation.mutate()}
            disabled={promoteMutation.isPending || !nodeId.trim()}
          >
            {promoteMutation.isPending ? "Promoting..." : "Promote to Primary"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function MembridgePage() {
  const [selectedCid, setSelectedCid] = useState<string | null>(null);
  const [selectedManagedProject, setSelectedManagedProject] = useState<ManagedProject | null>(null);

  const projectsQuery = useQuery<MembridgeProject[]>({
    queryKey: ["/api/membridge/projects"],
    refetchInterval: 30000,
  });

  const managedProjectsQuery = useQuery<ManagedProject[]>({
    queryKey: ["/api/runtime/projects"],
    refetchInterval: 15000,
  });

  const leadershipQuery = useQuery<LeadershipLease>({
    queryKey: ["/api/membridge/projects", selectedCid, "leadership"],
    enabled: !!selectedCid,
    refetchInterval: 30000,
  });

  const nodesQuery = useQuery<ProjectNode[]>({
    queryKey: ["/api/membridge/projects", selectedCid, "nodes"],
    enabled: !!selectedCid,
    refetchInterval: 15000,
  });

  const projects = projectsQuery.data || [];
  const managedProjects = managedProjectsQuery.data || [];
  const leadership = leadershipQuery.data || null;
  const nodes = nodesQuery.data || [];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold" data-testid="text-membridge-title">
            Membridge Control Plane
          </h1>
          <p className="text-muted-foreground mt-1">
            Multi-project git management, memory sync, and node orchestration
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" data-testid="text-git-management-title">
              <GitBranch className="h-5 w-5" />
              Git Repository Management
            </h2>
            <div className="space-y-4">
              <AddProjectForm />

              {managedProjectsQuery.isLoading ? (
                <div className="text-sm text-muted-foreground py-4">Loading managed projects...</div>
              ) : managedProjects.length === 0 ? (
                <Card>
                  <CardContent className="py-8">
                    <div className="text-center text-muted-foreground" data-testid="text-no-managed-projects">
                      <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      No managed projects yet. Add a repository above to get started.
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-3">
                  {managedProjects.map((mp) => (
                    <ManagedProjectCard
                      key={mp.id}
                      project={mp}
                      onSelect={() => setSelectedManagedProject(
                        selectedManagedProject?.id === mp.id ? null : mp
                      )}
                    />
                  ))}
                </div>
              )}

              {selectedManagedProject && (
                <>
                  <Separator />
                  <ManagedProjectDetail project={selectedManagedProject} />
                </>
              )}
            </div>
          </div>

          <Separator />

          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" data-testid="text-control-plane-title">
              <Crown className="h-5 w-5" />
              Membridge Control Plane
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
              <div>
                <ProjectList
                  projects={projects}
                  isLoading={projectsQuery.isLoading}
                  selectedCid={selectedCid}
                  onSelect={setSelectedCid}
                />
              </div>

              <div className="space-y-6">
                {!selectedCid ? (
                  <Card>
                    <CardContent className="py-12">
                      <div className="text-center text-muted-foreground" data-testid="text-select-project">
                        <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        Select a project from the list to view its leadership and nodes.
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <>
                    <LeadershipCard
                      cid={selectedCid}
                      leadership={leadership}
                      isLoading={leadershipQuery.isLoading}
                    />
                    <Separator />
                    <NodesTable
                      cid={selectedCid}
                      nodes={nodes}
                      isLoading={nodesQuery.isLoading}
                    />
                    <Separator />
                    <PromotePrimaryForm cid={selectedCid} />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
