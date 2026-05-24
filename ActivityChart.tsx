"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";

const data = [
  { name: "Mon", bugs: 12, tasks: 45 },
  { name: "Tue", bugs: 8, tasks: 52 },
  { name: "Wed", bugs: 15, tasks: 38 },
  { name: "Thu", bugs: 5, tasks: 65 },
  { name: "Fri", bugs: 9, tasks: 48 },
  { name: "Sat", bugs: 4, tasks: 25 },
  { name: "Sun", bugs: 2, tasks: 15 },
];

export default function ActivityChart() {
  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorTasks" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorBugs" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#101425', borderColor: 'rgba(255,255,255,0.05)', borderRadius: '12px', color: '#fff', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}
            itemStyle={{ color: '#F8FAFC' }}
            cursor={{ stroke: '#ffffff20', strokeWidth: 1, strokeDasharray: '3 3' }}
          />
          <Area type="monotone" dataKey="tasks" name="AI Tasks" stroke="#7C3AED" strokeWidth={3} fillOpacity={1} fill="url(#colorTasks)" />
          <Area type="monotone" dataKey="bugs" name="Bugs Fixed" stroke="#10B981" strokeWidth={3} fillOpacity={1} fill="url(#colorBugs)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}