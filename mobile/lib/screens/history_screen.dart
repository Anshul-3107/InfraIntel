import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../actions.dart';
import '../api_client.dart';
import '../models.dart';
import '../providers.dart';
import '../widgets.dart';
import 'result_screen.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  Future<void> _refresh(WidgetRef ref) async {
    ref.invalidate(historyProvider);
    try {
      await ref.read(historyProvider.future);
    } catch (_) {
      // The error is shown by the screen itself.
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(historyProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(historyProvider),
          ),
        ],
      ),
      body: history.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          final expired = error is ApiException && error.statusCode == 401;
          return _ErrorView(
            message: error is ApiException
                ? error.message
                : 'Could not load history.',
            actionLabel: expired ? 'Sign in again' : 'Retry',
            onAction: expired
                ? () => ref.read(authProvider.notifier).logout()
                : () => ref.invalidate(historyProvider),
          );
        },
        data: (items) => RefreshIndicator(
          onRefresh: () => _refresh(ref),
          child: items.isEmpty
              ? ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: const [
                    SizedBox(height: 160),
                    Center(child: Text('No inspections yet.')),
                  ],
                )
              : ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) =>
                      _InspectionTile(inspection: items[index]),
                ),
        ),
      ),
    );
  }
}

class _InspectionTile extends ConsumerWidget {
  const _InspectionTile({required this.inspection});

  final Inspection inspection;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final a = inspection.assessment;
    final count = inspection.detections.length;
    return ListTile(
      contentPadding: const EdgeInsets.only(left: 16, right: 4, top: 6, bottom: 6),
      leading: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: SizedBox(
          width: 56,
          height: 56,
          child: Image.network(
            inspection.imageUrl,
            fit: BoxFit.cover,
            cacheWidth: 160,
            errorBuilder: (_, _, _) => Container(
              color: Colors.black12,
              child: const Icon(Icons.broken_image),
            ),
          ),
        ),
      ),
      title: Row(
        children: [
          LevelTag(a.priority),
          const SizedBox(width: 8),
          Text('${a.score}/100'),
        ],
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Text(
          '${formatDateTime(inspection.createdAt)}\n'
          '${inspection.assetLabel} · $count detection${count == 1 ? '' : 's'}',
        ),
      ),
      isThreeLine: true,
      trailing: PopupMenuButton<String>(
        tooltip: 'More',
        onSelected: (value) {
          if (value == 'delete') {
            confirmAndDeleteInspection(context, ref, inspection);
          }
        },
        itemBuilder: (_) => const [
          PopupMenuItem(
            value: 'delete',
            child: Row(
              children: [
                Icon(Icons.delete_outline),
                SizedBox(width: 12),
                Text('Delete'),
              ],
            ),
          ),
        ],
      ),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultScreen(
            image: NetworkImage(inspection.imageUrl),
            inspection: inspection,
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 40),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onAction, child: Text(actionLabel)),
          ],
        ),
      ),
    );
  }
}