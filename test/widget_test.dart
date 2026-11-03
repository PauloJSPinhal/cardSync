import 'package:flutter_test/flutter_test.dart';
import 'package:cardsync_mobile/main.dart';

void main() {
  testWidgets('App builds', (WidgetTester tester) async {
    await tester.pumpWidget(const CardSyncApp());
    expect(find.text('cardSync'), findsOneWidget);
  });
}