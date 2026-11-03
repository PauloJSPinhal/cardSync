import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/naming.dart';
import '../core/manifest.dart';
import '../services/drive_service.dart';

class NewCollectionScreen extends StatefulWidget {
  const NewCollectionScreen({super.key});
  @override
  State<NewCollectionScreen> createState() => _NewCollectionScreenState();
}

class _NewCollectionScreenState extends State<NewCollectionScreen> {
  DateTime _date = DateTime.now();
  final _eventCtrl = TextEditingController();
  final _locCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  String _result = '';

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _create() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _result = '';
    });
    try {
      final ok = await DriveService.instance.init();
      if (!ok) throw Exception('Não autenticado. Faça login primeiro.');
      final ev = _eventCtrl.text.trim();
      final loc = _locCtrl.text.trim();
      final rootName = folderName(_date, ev, loc);
      final ids = await DriveService.instance.ensureStructure(rootName);
      final manifest = newManifest(projectId(_date, ev), rootName, displayTitle(_date, ev, loc));
      manifest['drive_ids'] = {
        'root_folder_id': ids['root'],
        'raw_folder_id': ids['01_RAW'],
        'jpg_folder_id': ids['02_JPG_Original'],
        'treated_folder_id': ids['03_Tratadas'],
        'docs_folder_id': ids['04_Docs'],
      };
      // guardar lista local
      final prefs = await SharedPreferences.getInstance();
      final list = prefs.getStringList('collections') ?? [];
      list.add(rootName);
      await prefs.setStringList('collections', list);
      setState(() => _result = 'Criada: $rootName\nroot: ${ids['root']}');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Coleção "$rootName" criada')),
        );
      }
    } catch (e) {
      setState(() => _result = 'Erro: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nova Coleção')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
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
              TextFormField(
                controller: _eventCtrl,
                decoration: const InputDecoration(labelText: 'Evento'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _locCtrl,
                decoration: const InputDecoration(labelText: 'Local'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _loading ? null : _create,
                icon: _loading
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.create_new_folder),
                label: Text(_loading ? 'A criar...' : 'Criar Coleção'),
              ),
              const SizedBox(height: 16),
              if (_result.isNotEmpty) SelectableText(_result),
            ],
          ),
        ),
      ),
    );
  }
}