import { Card } from "@/components/ui/card";
export function MetricCard({label,value}:{label:string;value:number}){return <Card><div className="muted">{label}</div><div className="score">{value}</div></Card>}
