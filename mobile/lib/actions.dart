import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'models.dart';
import 'providers.dart';

/// Asks for confirmation, then deletes [inspection] on the server.
/// Returns true if it is gone afterwards (deleted now, or already deleted),
/// false if the user cancelled or the delete failed.
Future<bool> confirmAndDeleteInspection(
  BuildContext context,
  WidgetRef ref,
  Inspection inspection,
) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: Text('Delete inspection #${inspection.id}?'),
      content: const Text(
        'This removes the photo and its results from the server and '
        'updates the asset\'s health score. This cannot be undone.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: Theme.of(dialogContext).colorScheme.error,
          ),
          onPressed: () => Navigator.of(dialogContext).pop(true),
          child: const Text('Delete'),
        ),
      ],
    ),
  );
  if (confirmed != true) return false;

  // The screen may have been closed while the dialog was open.
  if (!context.mounted) return false;
  final messenger = ScaffoldMessenger.of(context);

  try {
    await ref.read(apiProvider).deleteInspection(inspection.id);
  } on ApiException catch (e) {
    if (e.statusCode == 401) {
      await ref.read(authProvider.notifier).logout();
      return false;
    }
    if (e.statusCode == 404) {
      // Already gone, so just bring the lists up to date.
      ref.invalidate(historyProvider);
      ref.invalidate(assetsProvider);
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(content: Text('That inspection no longer exists.')),
        );
      return true;
    }
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(e.message)));
    return false;
  }

  // The list and the asset pins/health both change when an inspection goes.
  ref.invalidate(historyProvider);
  ref.invalidate(assetsProvider);
  messenger
    ..hideCurrentSnackBar()
    ..showSnackBar(const SnackBar(content: Text('Inspection deleted.')));
  return true;
}