import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../services/drive_service.dart';

class ShareScreen extends StatefulWidget {
  const ShareScreen({super.key});
  @override
  State<ShareScreen> createState() => _ShareScreenState();
}

class _ShareScreenState extends State<ShareScreen> {
  final _folderIdCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  bool _loading = false;
  String _log = '';

  String get _url => _folderIdCtrl.text.trim().isEmpty
      ? ''
      : DriveService.instance.folderUrl(_folderIdCtrl.text.trim());

  Future<void> _share() async {
    final id = _folderIdCtrl.text.trim();
    final email = _emailCtrl.text.trim();
    if (id.isEmpty || email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preencha ID da pasta e e-mail.')));
      return;
    }
    setState(() => _loading = true);
    try {
      final ok = await DriveService.instance.init();
      if (!ok) throw Exception('Não autenticado.');
      await DriveService.instance.createPermission(id, email);
      setState(() => _log = 'Permissão reader concedida a $email');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Partilhado com $email')));
      }
    } catch (e) {
      setState(() => _log = 'Erro: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Partilhar')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _folderIdCtrl,
              decoration: const InputDecoration(
                labelText: 'ID da pasta 03_Tratadas',
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            if (_url.isNotEmpty) ...[
              Center(child: QrImageView(data: _url, version: QrVersions.auto, size: 200)),
              const SizedBox(height: 8),
              SelectableText(_url, style: const TextStyle(fontSize: 12)),
              const SizedBox(height: 12),
            ],
            TextField(
              controller: _emailCtrl,
              decoration: const InputDecoration(labelText: 'E-mail do contacto', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _loading ? null : _share,
              icon: _loading
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.person_add),
              label: Text(_loading ? 'A partilhar...' : 'Partilhar (reader)'),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_log.isEmpty ? 'Log de partilha...' : _log),
            ),
          ],
        ),
      ),
    );
  }
}