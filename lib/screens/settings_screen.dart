import 'package:flutter/material.dart';
import '../services/drive_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _info = 'Não autenticado';
  bool _loading = false;

  Future<void> _check() async {
    setState(() => _loading = true);
    final ok = await DriveService.instance.init();
    if (!ok) {
      setState(() {
        _info = 'Não autenticado';
        _loading = false;
      });
      return;
    }
    final about = await DriveService.instance.about();
    setState(() {
      _info = about == null
          ? 'Autenticado, mas sem quota disponível'
          : 'Autenticado\nUsado: ${_fmt(about['used']!)} / ${_fmt(about['total']!)}';
      _loading = false;
    });
  }

  String _fmt(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Conta Google', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(_info),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: _loading ? null : _check,
                      icon: _loading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.refresh),
                      label: const Text('Verificar autenticação / quota'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Backend', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    const Text('Google Drive API v3 (OAuth2).'),
                    const Text('No desktop Linux, o login usa OAuth via navegador.'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}