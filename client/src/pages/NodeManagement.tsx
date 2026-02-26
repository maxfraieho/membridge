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
  Server,
  RefreshCw,
  Plus,
  Trash2,
  Download,
  ArrowUpCircle,
  RotateCcw,
  Heart,
  Terminal,
  Copy,
  Check,
  Loader2,
  Wifi,
  WifiOff,
  AlertCircle,
  XCircle,
} from "lucide-react";

interface WorkerNode {
  id: string;
  node_id: string;
  url: string;
  status: string;
  capabilities: { claude_cli: boolean; max_concurrency: number; labels: string[] };
  last_heartbeat: number | null;
  ip_addrs: string[];
  obs_count: number;
  db_sha: string;
  registered_at: number;
  active_leases: number;
  agent_version: string;
  os_info: string;
  install_method: string;
}

function formatRelative(ts: number | null) {
  if (!ts) return "—";
  const now = Date.now();
  const diff = now - ts;
  if (diff < 0) return "in the future";
  if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
  return `${Math.round(diff / 3600000)}h ago`;
}

function statusIcon(status: string) {
  switch (status) {
    case "online":
      return <Wifi className="h-4 w-4 text-green-500" />;
    case "offline":
      return <WifiOff className="h-4 w-4 text-muted-foreground" />;
    case "error":
      return <XCircle className="h-4 w-4 text-destructive" />;
    case "syncing":
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
  }
}

function statusBadge(status: string) {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    online: "default",
    offline: "secondary",
    error: "destructive",
    syncing: "outline",
    unknown: "outline",
  };
  return <Badge data-testid={`badge-status-${status}`} variant={variants[status] || "outline"}>{status}</Badge>;
}

function AddNodeForm() {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/runtime/workers", {
        name: name.trim(),
        url: url.trim(),
        status: "unknown",
      });
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      toast({ title: "Node registered", description: `"${data.id}" added to fleet.` });
      setName("");
      setUrl("");
    },
    onError: (err: Error) => {
      toast({ title: "Failed to register node", description: err.message, variant: "destructive" });
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Plus className="h-4 w-4" />
          Register Node
        </CardTitle>
        <CardDescription>
          Add a node to the fleet. The agent must be running on this node.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 max-w-lg">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="add-node-name">Node ID</Label>
              <Input
                id="add-node-name"
                data-testid="input-node-name"
                placeholder="e.g. rpi4b"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-node-url">Agent URL</Label>
              <Input
                id="add-node-url"
                data-testid="input-node-url"
                placeholder="http://192.168.3.161:8001"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          </div>
          <Button
            data-testid="button-register-node"
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending || !name.trim() || !url.trim()}
            className="w-fit"
          >
            {createMutation.isPending ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Registering...</>
            ) : (
              <><Plus className="h-4 w-4 mr-2" />Register Node</>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function InstallScriptCard() {
  const [copied, setCopied] = useState(false);
  const [serverUrl, setServerUrl] = useState("");
  const [nodeId, setNodeId] = useState("");

  const installCmd = `curl -sSL "${serverUrl || 'http://YOUR_SERVER:5000'}/api/runtime/agent-install-script${nodeId ? `?node_id=${nodeId}` : ''}" | bash`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(installCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Terminal className="h-4 w-4" />
          Install Agent on New Node
        </CardTitle>
        <CardDescription>
          Run this command on any Linux machine to install the Membridge agent.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 max-w-lg">
            <div className="space-y-2">
              <Label htmlFor="install-server-url">Control Plane URL</Label>
              <Input
                id="install-server-url"
                data-testid="input-install-server-url"
                placeholder="http://192.168.3.184:5000"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="install-node-id">Node ID (optional)</Label>
              <Input
                id="install-node-id"
                data-testid="input-install-node-id"
                placeholder="auto-detect hostname"
                value={nodeId}
                onChange={(e) => setNodeId(e.target.value)}
              />
            </div>
          </div>
          <div className="relative">
            <pre
              className="bg-muted rounded-md p-4 pr-12 text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all"
              data-testid="text-install-command"
            >
              {installCmd}
            </pre>
            <Button
              data-testid="button-copy-install"
              variant="ghost"
              size="sm"
              className="absolute top-2 right-2"
              onClick={copyToClipboard}
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Requirements: Python 3.11+, git, curl. Automatically sets up systemd or OpenRC service. Agent v0.4.0 supports self-update, restart, uninstall, and git clone operations.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function NodeActions({ worker }: { worker: WorkerNode }) {
  const { toast } = useToast();

  const healthMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("GET", `/api/runtime/workers/${worker.id}/agent-health`);
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      if (data.reachable) {
        toast({ title: "Agent healthy", description: `${worker.id}: v${data.version || "unknown"}, host=${data.hostname || "?"}` });
      } else {
        toast({ title: "Agent unreachable", description: data.error || "Connection failed", variant: "destructive" });
      }
    },
    onError: (err: Error) => {
      toast({ title: "Health check failed", description: err.message, variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", `/api/runtime/workers/${worker.id}/agent-update`, {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      toast({ title: "Update triggered", description: `Agent on ${worker.id} is updating...` });
    },
    onError: (err: Error) => {
      toast({ title: "Update failed", description: err.message, variant: "destructive" });
    },
  });

  const restartMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", `/api/runtime/workers/${worker.id}/agent-restart`, {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      toast({ title: "Restart triggered", description: `Agent on ${worker.id} is restarting.` });
    },
    onError: (err: Error) => {
      toast({ title: "Restart failed", description: err.message, variant: "destructive" });
    },
  });

  const uninstallMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", `/api/runtime/workers/${worker.id}/agent-uninstall`, {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      toast({ title: "Uninstalled", description: `Agent removed from ${worker.id}.` });
    },
    onError: (err: Error) => {
      toast({ title: "Uninstall failed", description: err.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("DELETE", `/api/runtime/workers/${worker.id}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] });
      toast({ title: "Node removed", description: `${worker.id} unregistered from fleet.` });
    },
    onError: (err: Error) => {
      toast({ title: "Delete failed", description: err.message, variant: "destructive" });
    },
  });

  const isBusy = healthMutation.isPending || updateMutation.isPending || restartMutation.isPending || uninstallMutation.isPending || deleteMutation.isPending;

  return (
    <div className="flex gap-1 flex-wrap">
      <Button
        data-testid={`button-health-${worker.id}`}
        variant="outline"
        size="sm"
        disabled={isBusy}
        onClick={() => healthMutation.mutate()}
        title="Check agent health"
      >
        {healthMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Heart className="h-3 w-3" />}
      </Button>
      <Button
        data-testid={`button-update-${worker.id}`}
        variant="outline"
        size="sm"
        disabled={isBusy}
        onClick={() => updateMutation.mutate()}
        title="Update agent (git pull + restart)"
      >
        {updateMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <ArrowUpCircle className="h-3 w-3" />}
      </Button>
      <Button
        data-testid={`button-restart-${worker.id}`}
        variant="outline"
        size="sm"
        disabled={isBusy}
        onClick={() => restartMutation.mutate()}
        title="Restart agent service"
      >
        {restartMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
      </Button>
      <Button
        data-testid={`button-uninstall-${worker.id}`}
        variant="outline"
        size="sm"
        disabled={isBusy}
        onClick={() => uninstallMutation.mutate()}
        title="Uninstall agent from node"
      >
        {uninstallMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3 rotate-180" />}
      </Button>
      <Button
        data-testid={`button-remove-node-${worker.id}`}
        variant="ghost"
        size="sm"
        disabled={isBusy}
        onClick={() => deleteMutation.mutate()}
        title="Remove node from fleet"
      >
        <Trash2 className="h-3 w-3 text-destructive" />
      </Button>
    </div>
  );
}

export default function NodeManagement() {
  const workersQuery = useQuery<WorkerNode[]>({
    queryKey: ["/api/runtime/workers"],
    refetchInterval: 15000,
  });

  const workers = workersQuery.data || [];
  const onlineCount = workers.filter(w => w.status === "online").length;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold" data-testid="text-nodes-title">
            Node & Agent Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Install, update, restart, and manage Membridge agents across your fleet
          </p>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <Server className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <div className="text-2xl font-bold" data-testid="text-total-nodes">{workers.length}</div>
                    <div className="text-xs text-muted-foreground">Total Nodes</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <Wifi className="h-8 w-8 text-green-500" />
                  <div>
                    <div className="text-2xl font-bold" data-testid="text-online-nodes">{onlineCount}</div>
                    <div className="text-xs text-muted-foreground">Online</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-3">
                  <WifiOff className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <div className="text-2xl font-bold" data-testid="text-offline-nodes">{workers.length - onlineCount}</div>
                    <div className="text-xs text-muted-foreground">Offline / Unknown</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Server className="h-4 w-4" />
                  Fleet Overview
                </CardTitle>
                <Button
                  data-testid="button-refresh-workers"
                  variant="ghost"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] })}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>{workers.length} node(s) in fleet</CardDescription>
            </CardHeader>
            <CardContent>
              {workersQuery.isLoading ? (
                <div className="text-sm text-muted-foreground py-4">Loading nodes...</div>
              ) : workers.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center" data-testid="text-no-workers">
                  <Server className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  No nodes registered. Use the install script or register a node manually below.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Node</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Agent Version</TableHead>
                      <TableHead>URL</TableHead>
                      <TableHead>IPs</TableHead>
                      <TableHead>Last Heartbeat</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workers.map((w) => (
                      <TableRow key={w.id} data-testid={`row-worker-${w.id}`}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {statusIcon(w.status)}
                            <div>
                              <div className="font-medium text-sm" data-testid={`text-worker-name-${w.id}`}>{w.id}</div>
                              {w.os_info && (
                                <div className="text-xs text-muted-foreground">{w.os_info}</div>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{statusBadge(w.status)}</TableCell>
                        <TableCell>
                          <span className="font-mono text-xs" data-testid={`text-version-${w.id}`}>
                            {w.agent_version === "unknown" ? (
                              <Badge variant="outline">unknown</Badge>
                            ) : w.agent_version === "uninstalled" ? (
                              <Badge variant="destructive">uninstalled</Badge>
                            ) : (
                              w.agent_version
                            )}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-mono text-xs">{w.url || "—"}</span>
                        </TableCell>
                        <TableCell>
                          {w.ip_addrs && w.ip_addrs.length > 0 ? (
                            <div className="flex gap-1 flex-wrap">
                              {w.ip_addrs.slice(0, 3).map((ip) => (
                                <Badge key={ip} variant="outline" className="text-xs font-mono">
                                  {ip}
                                </Badge>
                              ))}
                              {w.ip_addrs.length > 3 && (
                                <Badge variant="outline" className="text-xs">+{w.ip_addrs.length - 3}</Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">
                          {formatRelative(w.last_heartbeat)}
                        </TableCell>
                        <TableCell>
                          <NodeActions worker={w} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Separator />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InstallScriptCard />
            <AddNodeForm />
          </div>
        </div>
      </div>
    </div>
  );
}
