import 'package:flutter/material.dart';
import 'dart:math';

class BrailleActivity extends StatefulWidget {
  final String type; // 'searching', 'cracking', 'idle'
  final double size;

  const BrailleActivity({
    Key? key,
    required this.type,
    this.size = 24.0,
  }) : super(key: key);

  @override
  State<BrailleActivity> createState() => _BrailleActivityState();
}

class _BrailleActivityState extends State<BrailleActivity>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    final Duration duration = const Duration(milliseconds: 1500);
    if (widget.type == 'cracking') {
      _controller = AnimationController(vsync: this, duration: duration)..repeat();
    } else {
      _controller = AnimationController(vsync: this, duration: duration)
        ..repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final double value = _controller.value;
    int index;
    double opacity = 1.0;

    switch (widget.type) {
      case 'searching':
        // Circular motion: smooth back-and-forth scan
        index = (value * 255).round();
        break;
      case 'cracking':
        // Erratic/high-frequency: sawtooth wave with high frequency
        index = (value * 1000).floor() % 256;
        break;
      case 'idle':
        // Pulsing: slow index change + fast opacity pulse
        index =
            (sin(value * 2 * pi * 0.2) * 127.5 + 127.5).round(); // Slow index change
        opacity = (sin(value * 2 * pi * 2) + 1) / 2; // Fast opacity pulse (2x per cycle)
        break;
      default:
        index = 0;
    }

    // Clamp index to valid Braille range (0-255)
    index = index.clamp(0, 255);
    final String brailleChar = String.fromCharCode(0x2800 + index);

    return Container(
      width: widget.size,
      height: widget.size,
      child: Center(
        child: Text(
          brailleChar,
          style: TextStyle(
            fontSize: widget.size,
            color: Colors.white.withOpacity(opacity),
          ),
        ),
      ),
    );
  }
}