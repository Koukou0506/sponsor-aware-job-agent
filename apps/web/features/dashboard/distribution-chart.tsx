"use client";
import { ResponsiveContainer,BarChart,Bar,XAxis,YAxis,Tooltip } from "recharts"; import { Card } from "@/components/ui/card";
export function DistributionChart({title,data}:{title:string;data:Array<{key:string;count:number}>}){return <Card><h3>{title}</h3><div style={{height:220}}><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><XAxis dataKey="key"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="count" fill="#334155" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div></Card>}
