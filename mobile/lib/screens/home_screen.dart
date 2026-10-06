import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../api_client.dart';
import '../place.dart';
import '../providers.dart';
import 'result_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _picker = ImagePicker();
  File? _file;
  Position? _position;
  String? _locationError;
  bool _locating = false;
  bool _uploading = false;

  PlaceName? _place;
  bool _placeLoading = false;
  int _placeRequest = 0; // lets a late lookup be ignored after the photo changes

  /// Discards the chosen photo and its location. Does not touch the
  /// phone's own gallery, only what this screen is holding.
  void _clear() {
    _placeRequest++;
    setState(() {
      _file = null;
      _position = null;
      _locationError = null;
      _locating = false;
      _place = null;
      _placeLoading = false;
    });
  }

  Future<void> _pick(ImageSource source) async {
    final picked = await _picker.pickImage(
      source: source,
      imageQuality: 85,
      maxWidth: 1920,
      maxHeight: 1920,
    );
    if (picked == null) return;
    _placeRequest++;
    setState(() {
      _file = File(picked.path);
      _position = null;
      _locationError = null;
      _place = null;
      _placeLoading = false;
    });
    await _locate();
  }

  Future<Position> _currentPosition() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw Exception('Location services are turned off.');
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw Exception('Location permission is required to record the inspection.');
    }
    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: 20),
      ),
    );
  }

  Future<void> _locate() async {
    final photoAtStart = _file;
    setState(() {
      _locating = true;
      _locationError = null;
    });
    try {
      final pos = await _currentPosition();
      // Ignore the result if the photo was removed or replaced meanwhile.
      if (mounted && identical(_file, photoAtStart) && _file != null) {
        setState(() => _position = pos);
        unawaited(_lookupPlace(pos));
      }
    } on TimeoutException {
      if (mounted && identical(_file, photoAtStart) && _file != null) {
        setState(() => _locationError = 'Could not get a GPS fix in time.');
      }
    } catch (e) {
      if (mounted && identical(_file, photoAtStart) && _file != null) {
        setState(() =>
            _locationError = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  Future<void> _lookupPlace(Position pos) async {
    final request = ++_placeRequest;
    setState(() {
      _place = null;
      _placeLoading = true;
    });
    final place = await lookupPlaceName(pos.latitude, pos.longitude);
    if (!mounted || request != _placeRequest) return;
    setState(() {
      _place = place;
      _placeLoading = false;
    });
  }

  Future<void> _analyze() async {
    final file = _file;
    final pos = _position;
    if (file == null || pos == null) return;

    setState(() => _uploading = true);
    try {
      final inspection = await ref.read(apiProvider).uploadInspection(
            imagePath: file.path,
            latitude: pos.latitude,
            longitude: pos.longitude,
          );
      // Make History and Map pick up the new inspection.
      ref.invalidate(historyProvider);
      ref.invalidate(assetsProvider);
      if (!mounted) return;
      // The photo has been submitted, so reset the screen for the next one.
      _clear();
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultScreen(
            image: FileImage(file),
            inspection: inspection,
          ),
        ),
      );
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        await ref.read(authProvider.notifier).logout();
        return;
      }
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  void _snack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final username = ref.watch(authProvider).value;
    final canAnalyze = _file != null && _position != null && !_uploading;

    return Scaffold(
      appBar: AppBar(
        title: const Text('New inspection'),
        actions: [
          if (username != null)
            Center(child: Text(username, style: theme.textTheme.bodyMedium)),
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: _uploading
                ? null
                : () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    color: theme.colorScheme.surfaceContainerHighest,
                    child: _file == null
                        ? const Center(
                            child: Text('Take or choose a photo of the road'),
                          )
                        : Stack(
                            fit: StackFit.expand,
                            children: [
                              Image.file(_file!, fit: BoxFit.contain),
                              Positioned(
                                top: 8,
                                right: 8,
                                child: IconButton.filled(
                                  tooltip: 'Remove photo',
                                  style: IconButton.styleFrom(
                                    backgroundColor: Colors.black54,
                                    foregroundColor: Colors.white,
                                  ),
                                  icon: const Icon(Icons.close),
                                  onPressed: _uploading ? null : _clear,
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              _LocationRow(
                locating: _locating,
                position: _position,
                place: _place,
                placeLoading: _placeLoading,
                error: _locationError,
                hasPhoto: _file != null,
                onRetry: _locate,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed:
                          _uploading ? null : () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.photo_camera),
                      label: const Text('Camera'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed:
                          _uploading ? null : () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library),
                      label: const Text('Gallery'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: canAnalyze ? _analyze : null,
                icon: _uploading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.analytics),
                label: Text(_uploading ? 'Analyzing...' : 'Analyze'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LocationRow extends StatelessWidget {
  const _LocationRow({
    required this.locating,
    required this.position,
    required this.place,
    required this.placeLoading,
    required this.error,
    required this.hasPhoto,
    required this.onRetry,
  });

  final bool locating;
  final Position? position;
  final PlaceName? place;
  final bool placeLoading;
  final String? error;
  final bool hasPhoto;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (locating) {
      return const Row(
        children: [
          SizedBox(
              height: 16,
              width: 16,
              child: CircularProgressIndicator(strokeWidth: 2)),
          SizedBox(width: 8),
          Text('Getting location...'),
        ],
      );
    }
    if (position != null) {
      final title = place?.title ??
          (placeLoading ? 'Finding place name...' : 'Place name unavailable');
      final coords =
          '${position!.latitude.toStringAsFixed(5)}, ${position!.longitude.toStringAsFixed(5)}';
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 2),
            child: Icon(Icons.place, size: 18),
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
                if (place?.subtitle != null)
                  Text(place!.subtitle!, style: theme.textTheme.bodySmall),
                Text(
                  coords,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.outline),
                ),
              ],
            ),
          ),
          TextButton(onPressed: onRetry, child: const Text('Refresh')),
        ],
      );
    }
    if (error != null) {
      return Row(
        children: [
          Icon(Icons.location_off, size: 18, color: theme.colorScheme.error),
          const SizedBox(width: 6),
          Expanded(
            child: Text(error!, style: TextStyle(color: theme.colorScheme.error)),
          ),
          TextButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      );
    }
    return Text(
      hasPhoto
          ? 'Location not captured yet.'
          : 'Location is recorded when you pick a photo.',
      style: theme.textTheme.bodySmall,
    );
  }
}