import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis_auth/auth_io.dart' as auth_io;
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

class AuthService {
  static final AuthService instance = AuthService._();
  AuthService._();

  GoogleSignIn? _gsi;
  GoogleSignInAccount? _account;
  http.Client? _desktopClient;

  bool get isSignedIn => _account != null || _desktopClient != null;
  String? get userEmail => _account?.email;

  Future<void> init() async {
    if (kIsWeb) return;
    if (Platform.isAndroid || Platform.isIOS) {
      _gsi = GoogleSignIn.instance;
      await _gsi!.initialize();
      try {
        _account = await _gsi!.attemptLightweightAuthentication();
      } catch (_) {
        _account = null;
      }
    }
    // desktop: lazy, via signIn()
  }

  Future<bool> signIn() async {
    if (Platform.isAndroid || Platform.isIOS) {
      if (_gsi == null) {
        _gsi = GoogleSignIn.instance;
        await _gsi!.initialize();
      }
      try {
        _account = await _gsi!.authenticate();
        return _account != null;
      } catch (_) {
        return false;
      }
    }
    // Desktop OAuth via browser
    try {
      final clientId = auth_io.ClientId(
        // Substitua pelo seu client ID OAuth desktop, ou use o do projeto
        'YOUR_DESKTOP_CLIENT_ID.apps.googleusercontent.com',
        null,
      );
      // Sem client secret para installed app
      _desktopClient = await auth_io.clientViaUserConsent(
        clientId,
        ['https://www.googleapis.com/auth/drive'],
        (url) async {
          final uri = Uri.parse(url);
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          }
        },
      );
      return _desktopClient != null;
    } catch (e) {
      return false;
    }
  }

  Future<void> signOut() async {
    await _gsi?.signOut();
    _account = null;
    _desktopClient?.close();
    _desktopClient = null;
  }

  /// Retorna um http.Client autenticado, ou null.
  Future<http.Client?> authenticatedClient() async {
    if (_desktopClient != null) return _desktopClient;
    if (_account != null) {
      final authz = await _account!.authorizationClient.authorizeScopes([
        'https://www.googleapis.com/auth/drive',
      ]);
      final token = authz.accessToken;
      return _BearerClient(token, http.Client());
    }
    return null;
  }
}

class _BearerClient extends http.BaseClient {
  _BearerClient(this._token, this._inner);
  final String _token;
  final http.Client _inner;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    request.headers['Authorization'] = 'Bearer $_token';
    return _inner.send(request);
  }
}