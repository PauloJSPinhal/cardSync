import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/auth_service.dart';
import '../services/drive_service.dart';
import 'new_collection_screen.dart';
import 'import_screen.dart';
import 'share_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;
  String _status = 'Não autenticado';
  bool _loading = false;

  final _pages = const [
    _HomePage(),
    ImportScreen(),
    ShareScreen(),
    SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _status = prefs.getString('status') ?? 'Não autenticado');
  }

  Future<void> _signIn() async {
    setState(() => _loading = true);
    final ok = await AuthService.instance.signIn();
    if (ok) {
      await DriveService.instance.init();
      final about = await DriveService.instance.about();
      setState(() {
        _status = 'Logado${AuthService.instance.userEmail != null ? ': ${AuthService.instance.userEmail}' : ''}';
        if (about != null) {
          _status += ' • Quota: ${_fmt(about['used'])}/${_fmt(about['total'])}';
        }
      });
    } else {
      setState(() => _status = 'Falha no login');
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('status', _status);
    setState(() => _loading = false);
  }

  String _fmt(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('cardSync'),
        actions: [
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(12),
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
            ),
          IconButton(
            tooltip: 'Entrar com Google',
            onPressed: _loading ? null : _signIn,
            icon: const Icon(Icons.login),
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: cs.primaryContainer,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(_status, style: TextStyle(color: cs.onPrimaryContainer)),
          ),
          Expanded(child: _pages[_index]),
        ],
      ),
      floatingActionButton: _index == 0
          ? FloatingActionButton.extended(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NewCollectionScreen())),
              icon: const Icon(Icons.add),
              label: const Text('Nova Coleção'),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Início'),
          NavigationDestination(icon: Icon(Icons.upload_file_outlined), selectedIcon: Icon(Icons.upload_file), label: 'Importar'),
          NavigationDestination(icon: Icon(Icons.share_outlined), selectedIcon: Icon(Icons.share), label: 'Partilhar'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Config'),
        ],
      ),
    );
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage();
  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Bem-vindo ao cardSync', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                const Text('Gestor de arquivo e partilha fotográfica no Google Drive.'),
                const SizedBox(height: 8),
                const Text('Use "Nova Coleção" para começar. Importe fotos e partilhe a subpasta 03_Tratadas.'),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Card(
          child: ListTile(
            leading: const Icon(Icons.folder_special),
            title: const Text('Coleções'),
            subtitle: const Text('Lista de coleções criadas localmente'),
            trailing: const Icon(Icons.chevron_right),
          ),
        ),
      ],
    );
  }
}