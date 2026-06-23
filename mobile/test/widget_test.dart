import 'package:flutter_test/flutter_test.dart';

import 'package:ets_live/main.dart';

void main() {
  testWidgets('App launches', (WidgetTester tester) async {
    await tester.pumpWidget(const EtsLiveApp());
    expect(find.text('ETS Live Malaysia'), findsOneWidget);
  });
}
