import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/websocket_service.dart';
import '../widgets/liquid_glass_card.dart';
import '../widgets/braille_activity.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Connect to your FastAPI backend
    Future.microtask(() =>
        context.read<WebSocketService>().connect('ws://localhost:8000/ws'));
  }

  @override
  Widget build(BuildContext context) {
    final ws = context.watch<WebSocketService>();

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Background Glow
          Positioned(
            top: -100,
            right: -100,
            child: Container(width: 300, height: 300, decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.blue.withOpacity(0.15), blurRadius: 100)),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  _buildHeader(ws),
                  const SizedBox(height: 20),
                  Expanded(child: _buildLogTerminal(ws)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(WebSocketService ws) {
    return LiquidGlassCard(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("WIFITE2 BRIDGE", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2)),
              Text(ws.currentStatus, style: TextStyle(color: ws.currentStatus == "Connected" ? Colors.green : Colors.red, fontSize: 12)),
            ],
          ),
          IconButton(
            onPressed: () => ws.sendCommand(ws.isScanning ? "stop" : "start"),
            icon: Icon(ws.isScanning ? Icons.stop_circle : Icons.play_circle, color: Colors.white, size: 40),
          ),
        ],
      ),
    );
  }

  Widget _buildLogTerminal(WebSocketService ws) {
    return LiquidGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text("LIVE FEED", style: TextStyle(fontSize: 12, color: Colors.grey)),
              const Spacer(),
              if (ws.isScanning) const BrailleActivity(state: 'searching'),
            ],
          ),
          const Divider(color: Colors.white10),
          Expanded(
            child: ListView.builder(
              itemCount: ws.logs.length,
              itemBuilder: (context, i) => Text(
                ws.logs[i],
                style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: Colors.white70),
              ),
            ),
          ),
        ],
      ),
    );
  }
}