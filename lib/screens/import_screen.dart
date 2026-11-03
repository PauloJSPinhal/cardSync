import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import '../core/hashing.dart';
import '../core/importer.dart' as imp;
import '../services/drive_service.dart';

class ImportScreen extends StatefulWidget {
  const ImportScreen({super.key});
  @override
  State<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends State<ImportScreen> {
  DateTime _date = DateTime.now();
  final _eventCtrl = TextEditingController();
  final _locCtrl = TextEditingController();
  List<String> _files = [];
  bool _treated = false;
  bool _dedup = true;
  bool _loading = false;
  double _progress = 0;
  String _log = '';

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _pickFiles() async {
    final res = await FilePicker.pickFiles();
    if (res.isNotEmpty) {
      setState(() => _files = res.map((f) => f.path).whereType<String>().toList());
    }
  }

  Future<void> _run() async {
    if (_files.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Selecione ficheiros.')));
      return;
    }
    if (_eventCtrl.text.trim().isEmpty || _locCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preencha evento e local.')));
      return;
    }
    setState(() {
      _loading = true;
      _progress = 0;
      _log = '';
    });
    try {
      final ok = await DriveService.instance.init();
      if (!ok) throw Exception('Não autenticado.');
      final ev = _eventCtrl.text.trim();
      final loc = _locCtrl.text.trim();
      // agrupar por data de captura (aqui simplificado: usa data do formulário)
      final grouped = imp.groupFiles(_files, ev, loc, targetDate: _date, treated: _treated);
      int total = grouped.values.fold(0, (a, b) => a + b.values.fold(0, (c, d) => c + d.length));
      int done = 0;
      int uploaded = 0;
      int skipped = 0;
      for (final root in grouped.keys) {
        final ids = await DriveService.instance.ensureStructure(root);
        for (final sub in grouped[root]!.keys) {
          final folderId = sub == '01_RAW'
              ? ids['01_RAW']!
              : sub == '02_JPG_Original'
                  ? ids['02_JPG_Original']!
                  : ids['03_Tratadas']!;
          // inventário remoto para dedup
          List<String> remoteMd5 = [];
          if (_dedup) {
            final remote = await DriveService.instance.listFiles(folderId);
            remoteMd5 = remote.map((f) => f.md5Checksum ?? '').toList();
          }
          for (final localPath in grouped[root]![sub]!) {
            final fname = localPath.split(Platform.pathSeparator).last;
            final localMd5 = md5File(localPath);
            if (_dedup && remoteMd5.contains(localMd5)) {
              skipped++;
            } else {
              await DriveService.instance.uploadFile(localPath, folderId, filename: fname);
              uploaded++;
            }
            done++;
            setState(() {
              _progress = total > 0 ? done / total : 1;
              _log = '$fname: ${_dedup && remoteMd5.contains(localMd5) ? 'ignorado' : 'enviado'}';
            });
          }
        }
      }
      setState(() => _log = 'Concluído: total=$total enviados=$uploaded ignorados=$skipped');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Importação concluída: $uploaded enviados, $skipped ignorados')),
        );
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
      appBar: AppBar(title: const Text('Importar')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            InkWell(
              onTap: _pickDate,
              child: InputDecorator(
                decoration: const InputDecoration(labelText: 'Data do projeto', border: OutlineInputBorder()),
                child: Text('${_date.day.toString().padLeft(2, '0')}/${_date.month.toString().padLeft(2, '0')}/${_date.year}'),
              ),
            ),
            const SizedBox(height: 12),
            TextField(controller: _eventCtrl, decoration: const InputDecoration(labelText: 'Evento', border: OutlineInputBorder())),
            const SizedBox(height: 12),
            TextField(controller: _locCtrl, decoration: const InputDecoration(labelText: 'Local', border: OutlineInputBorder())),
            const SizedBox(height: 12),
            SwitchListTile(
              title: const Text('Fotos tratadas (03_Tratadas)'),
              value: _treated,
              onChanged: (v) => setState(() => _treated = v),
            ),
            SwitchListTile(
              title: const Text('Deduplicar por MD5'),
              value: _dedup,
              onChanged: (v) => setState(() => _dedup = v),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _pickFiles,
              icon: const Icon(Icons.attach_file),
              label: Text('Selecionar ficheiros (${_files.length})'),
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _loading ? null : _run,
              icon: _loading
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.cloud_upload),
              label: Text(_loading ? 'A enviar...' : 'Importar / Enviar'),
            ),
            const SizedBox(height: 12),
            if (_loading) LinearProgressIndicator(value: _progress),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_log.isEmpty ? 'Log de importação...' : _log),
            ),
          ],
        ),
      ),
    );
  }
}