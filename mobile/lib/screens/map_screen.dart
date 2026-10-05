import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../api_client.dart';
import '../models.dart';
import '../providers.dart';
import '../style.dart';
import '../widgets.dart';

class MapScreen extends ConsumerWidget {
  const MapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assets = ref.watch(assetsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Asset map'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(assetsProvider),
          ),
        ],
      ),
      body: assets.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          final expired = error is ApiException && error.statusCode == 401;
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off, size: 40),
                  const SizedBox(height: 12),
                  Text(
                    error is ApiException
                        ? error.message
                        : 'Could not load assets.',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: expired
                        ? () => ref.read(authProvider.notifier).logout()
                        : () => ref.invalidate(assetsProvider),
                    child: Text(expired ? 'Sign in again' : 'Retry'),
                  ),
                ],
              ),
            ),
          );
        },
        data: (list) => list.isEmpty
            ? const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'No assets yet. Assets appear here after your first inspection.',
                    textAlign: TextAlign.center,
                  ),
                ),
              )
            : _AssetMap(assets: list),
      ),
    );
  }
}

class _AssetMap extends StatelessWidget {
  const _AssetMap({required this.assets});

  final List<Asset> assets;

  @override
  Widget build(BuildContext context) {
    final points =
        assets.map((a) => LatLng(a.latitude, a.longitude)).toList();
    final singleSpot = points.toSet().length == 1;

    final options = singleSpot
        ? MapOptions(initialCenter: points.first, initialZoom: 16)
        : MapOptions(
            initialCameraFit: CameraFit.bounds(
              bounds: LatLngBounds.fromPoints(points),
              padding: const EdgeInsets.all(56),
              maxZoom: 17,
            ),
          );

    return Stack(
      children: [
        FlutterMap(
          options: options,
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.infraintel.infraintel_app',
            ),
            MarkerLayer(
              markers: [
                for (final a in assets)
                  Marker(
                    point: LatLng(a.latitude, a.longitude),
                    width: 44,
                    height: 44,
                    alignment: Alignment.topCenter,
                    child: GestureDetector(
                      onTap: () => _showAssetSheet(context, a),
                      child: Icon(
                        Icons.location_pin,
                        size: 44,
                        color: levelColor(a.health?.riskLevel ?? ''),
                      ),
                    ),
                  ),
              ],
            ),
            const RichAttributionWidget(
              attributions: [
                TextSourceAttribution('OpenStreetMap contributors'),
              ],
            ),
          ],
        ),
        const Positioned(left: 12, top: 12, child: _Legend()),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    const levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Asset risk', style: Theme.of(context).textTheme.labelSmall),
            const SizedBox(height: 4),
            for (final l in levels)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 1),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircleAvatar(radius: 5, backgroundColor: levelColor(l)),
                    const SizedBox(width: 6),
                    Text(l, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

void _showAssetSheet(BuildContext context, Asset asset) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheetContext) {
      final theme = Theme.of(sheetContext);
      final h = asset.health;
      final facts = <String>[
        asset.assetType[0].toUpperCase() + asset.assetType.substring(1),
        if (asset.constructionYear != null) 'built ${asset.constructionYear}',
        '${asset.latitude.toStringAsFixed(5)}, ${asset.longitude.toStringAsFixed(5)}',
      ];
      return ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(sheetContext).size.height * 0.8,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(asset.label, style: theme.textTheme.titleLarge),
                const SizedBox(height: 2),
                Text(facts.join(' · '), style: theme.textTheme.bodySmall),
                const SizedBox(height: 12),
                if (h != null)
                  ScoreCard(
                    title: 'Asset health',
                    score: h.score,
                    level: h.riskLevel,
                    levelLabel: '${h.riskLevel} risk',
                    subtitle:
                        'Trend: ${h.trend} · ${h.inspectionsConsidered} inspection(s) considered',
                    reasons: h.reasons,
                  )
                else
                  const Text('No inspections for this asset yet.'),
                if (asset.recent.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text('Recent inspections', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 4),
                  for (final r in asset.recent)
                    ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: Text(formatDateTime(r.createdAt)),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('${r.severityScore}/100'),
                          const SizedBox(width: 8),
                          LevelTag(r.priority),
                        ],
                      ),
                    ),
                ],
              ],
            ),
          ),
        ),
      );
    },
  );
}