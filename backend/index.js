import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { Console } from 'console';
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();
app.use(cors());
app.use(express.json());

const MCP_FILE = path.join(__dirname, 'mcps.json');

// Helper to read MCPs
function readMCPs() {
  if (!fs.existsSync(MCP_FILE)) return [];
  const data = fs.readFileSync(MCP_FILE);
  try {
    return JSON.parse(data);
  } catch {
    return [];
  }
}

// Helper to write MCPs
function writeMCPs(mcps) {
  fs.writeFileSync(MCP_FILE, JSON.stringify(mcps, null, 2));
}

// List all MCPs
app.get('/api/mcps', (req, res) => {
  try {
    const mcps = readMCPs();
    res.json(mcps);
  } catch (err) {
    res.status(500).json({ error: 'Failed to read MCPs' });
  }
});

// Add a new MCP
app.post('/api/mcps', (req, res) => {
  const { name, command, args } = req.body;
  if (!name || !command || !Array.isArray(args)) {
    return res.status(400).json({ error: 'Name, command, and args (array) are required' });
  }
  try {
    const mcps = readMCPs();
    const id = Date.now().toString();
    const newMCP = { id, name, command, args };
    mcps.push(newMCP);
    writeMCPs(mcps);
    res.status(201).json(newMCP);
  } catch (err) {
    res.status(500).json({ error: 'Failed to add MCP' });
  }
});

// Update an MCP
app.put('/api/mcps/:id', (req, res) => {
  const { id } = req.params;
  const { name, command, args } = req.body;
  try {
    const mcps = readMCPs();
    const idx = mcps.findIndex(m => m.id === id);
    if (idx === -1) return res.status(404).json({ error: 'MCP not found' });
    if (name) mcps[idx].name = name;
    if (command) mcps[idx].command = command;
    if (Array.isArray(args)) mcps[idx].args = args;
    writeMCPs(mcps);
    res.json(mcps[idx]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update MCP' });
  }
});

// Delete an MCP
app.delete('/api/mcps/:id', (req, res) => {
  const { id } = req.params;
  try {
    let mcps = readMCPs();
    const idx = mcps.findIndex(m => m.id === id);
    if (idx === -1) return res.status(404).json({ error: 'MCP not found' });
    const deleted = mcps.splice(idx, 1)[0];
    writeMCPs(mcps);
    res.json(deleted);
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete MCP' });
  }
});

const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

// LLM Proxy endpoint (HTTP MCP client with OpenAI fallback)
app.post('/api/llm', async (req, res) => {
  const { prompt, mcpId, openaiKey } = req.body;
  if (!prompt || !openaiKey) return res.status(400).json({ error: 'Prompt and openaiKey are required' });
  // If mcpId is not provided, call OpenAI directly
  if (!mcpId) {
    try {
      const openaiRes = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openaiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-4o',
          messages: [{ role: 'user', content: prompt }]
        })
      });
      const openaiData = await openaiRes.json();
      if (openaiData.choices && openaiData.choices[0]) {
        return res.json({ reply: openaiData.choices[0].message.content });
      } else {
        return res.status(500).json({ error: 'OpenAI API error', details: openaiData });
      }
    } catch (err) {
      return res.status(500).json({ error: 'Failed to contact OpenAI', details: err.message });
    }
  }
  try {
    const mcps = readMCPs();
    const mcp = mcps.find(m => m.id === mcpId);
    if (!mcp) return res.status(404).json({ error: 'MCP not found' });
    const endpoint = mcp.args[0];
    // HTTP MCP
    if (endpoint && endpoint.startsWith('http')) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, openaiKey })
        });
        if (response.ok) {
          const data = await response.json();
          return res.json({ reply: data.reply || data.response || JSON.stringify(data) });
        }
      } catch (err) {
        console.log("vvsdfvdsvf"+err);
      }
    } else if (mcp.command && Array.isArray(mcp.args)) {
      // Official MCP SDK integration
      try {
        const transport = new StdioClientTransport({
          command: "uv",
          args: [
            "run",
            "--with",
            "mcp[cli]",
            "mcp",
            "run",
            "D:\\Development\\mcp\\mymcpserver\\weathermcp\\server\\weather.py"
          ],

        });
      
        const client = new Client(
          { name: "mcp-client", version: "1.0.0" },
          { capabilities: {} }
        );
        await client.connect(transport);
        // List tools for debugging
        const toolsResponse = await client.request({ method: "tools/list" });
        console.log("Available tools:", toolsResponse.tools.map(t => t.name));
        // Call the tool (e.g., get_alerts)
        const result = await client.request({
          method: "tools/call",
          params: {
            name: "get_alerts",
            args: { state: "CA" }, // or parse from prompt
          },
        });
        await transport.close();
        res.json({ reply: result });
        return;
      } catch (err) {
        console.error("MCP SDK error:", err);
        res.status(500).json({ error: "MCP SDK error", details: err.message });
        return;
      }
    }
    // Fallback: call OpenAI directly
    try {
      const openaiRes = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openaiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-4o',
          messages: [{ role: 'user', content: prompt }]
        })
      });
      const openaiData = await openaiRes.json();
      if (openaiData.choices && openaiData.choices[0]) {
        return res.json({ reply: openaiData.choices[0].message.content });
      } else {
        return res.status(500).json({ error: 'OpenAI API error', details: openaiData });
      }
    } catch (err) {
      return res.status(500).json({ error: 'Failed to contact MCP server and OpenAI', details: err.message });
    }
  } catch (err) {
    res.status(500).json({ error: 'Failed to contact MCP server', details: err.message });
  }
});

const PORT = 4000;
app.listen(PORT, () => console.log('Backend running on port', PORT)); 
app.listen(PORT, () => console.log('Backend running on port', PORT)); 