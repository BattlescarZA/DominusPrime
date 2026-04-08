# Multimodal Memory System Tests

Comprehensive test suite for the DominusPrime v0.9.8 Multimodal Memory Enhancement.

## Test Structure

```
tests/memory/
├── conftest.py              # Shared fixtures and test utilities
├── test_storage.py          # Storage manager unit tests (18 tests)
├── test_processor.py        # Media processor unit tests (23 tests)
├── test_embedder.py         # Content embedder unit tests (31 tests)
├── test_index.py            # FAISS index unit tests (18 tests)
├── test_retrieval.py        # Retrieval system unit tests (25 tests)
├── test_proactive.py        # Proactive delivery unit tests (43 tests)
└── test_integration.py      # End-to-end integration tests (15 tests)
```

**Total: 173 tests**

## Test Coverage

### Storage Manager Tests (`test_storage.py`)
- ✅ Initialization and directory structure
- ✅ Storing images, videos, audio, documents
- ✅ Storage quota enforcement
- ✅ Media deletion and cleanup
- ✅ Thumbnail generation
- ✅ Duplicate handling
- ✅ Concurrent storage operations
- ✅ Error handling (invalid paths, missing files)

### Media Processor Tests (`test_processor.py`)
- ✅ Image processing and metadata extraction
- ✅ Video frame extraction
- ✅ Audio duration extraction
- ✅ Document content extraction
- ✅ EXIF data extraction
- ✅ File hash calculation
- ✅ Media type detection
- ✅ OCR text extraction (when enabled)
- ✅ Corrupted file handling
- ✅ Batch and concurrent processing

### Content Embedder Tests (`test_embedder.py`)
- ✅ CLIP embedder initialization
- ✅ Simple embedder fallback
- ✅ Image embedding generation
- ✅ Text embedding generation
- ✅ Embedding normalization
- ✅ Deterministic behavior
- ✅ Batch embedding operations
- ✅ Cross-modal compatibility
- ✅ Performance benchmarks
- ✅ Edge cases (empty text, unicode, special chars)

### FAISS Index Tests (`test_index.py`)
- ✅ Index initialization
- ✅ Adding/removing embeddings
- ✅ Similarity search (top-k)
- ✅ Multiple embedding types
- ✅ Index persistence (save/load)
- ✅ Batch operations
- ✅ Distance scoring
- ✅ Concurrent access
- ✅ Index rebuilding
- ✅ Dimension validation

### Retrieval System Tests (`test_retrieval.py`)
- ✅ Text-to-media search
- ✅ Media-to-media similarity search
- ✅ Session filtering
- ✅ Media type filtering
- ✅ Time range filtering
- ✅ Relevance ranking
- ✅ Cross-modal search
- ✅ Batch search operations
- ✅ Performance benchmarks
- ✅ Edge cases (empty queries, special chars)

### Proactive Delivery Tests (`test_proactive.py`)
- ✅ Context monitoring and analysis
- ✅ Keyword extraction
- ✅ Topic detection
- ✅ Entity recognition
- ✅ Intent detection
- ✅ Relevance scoring (multi-signal)
- ✅ Memory selection
- ✅ Delivery throttling
- ✅ Quota enforcement
- ✅ Duplicate prevention
- ✅ Full pipeline integration

### Integration Tests (`test_integration.py`)
- ✅ End-to-end storage and retrieval
- ✅ Multiple media types workflow
- ✅ Cross-modal search workflows
- ✅ Session isolation
- ✅ Storage quota enforcement
- ✅ Memory deletion
- ✅ Session cleanup
- ✅ Statistics reporting
- ✅ Concurrent operations
- ✅ Data persistence
- ✅ Proactive delivery pipeline
- ✅ Error handling
- ✅ Performance testing
- ✅ Data integrity

## Running Tests

### Run All Tests
```bash
pytest tests/memory/ -v
```

### Run Specific Test File
```bash
pytest tests/memory/test_storage.py -v
```

### Run Tests with Coverage
```bash
pytest tests/memory/ --cov=dominusprime.agents.memory --cov-report=html
```

### Run Tests in Parallel
```bash
pytest tests/memory/ -n auto
```

### Run Only Unit Tests (exclude integration)
```bash
pytest tests/memory/ -v -k "not integration"
```

### Run Only Integration Tests
```bash
pytest tests/memory/test_integration.py -v
```

### Run Tests with Specific Markers
```bash
# Skip tests requiring CLIP
pytest tests/memory/ -v -m "not skipif"

# Run only async tests
pytest tests/memory/ -v -k "asyncio"
```

## Test Fixtures

### Shared Fixtures (from `conftest.py`)
- `temp_dir` - Temporary directory for test files
- `sample_image` - Basic test image (100x100 red square)
- `sample_image_with_text` - Image with text for OCR testing
- `sample_video` - Minimal MP4 file
- `sample_audio` - Minimal MP3 file
- `sample_document` - Text document
- `large_image` - Large image (2000x2000) for quota testing
- `corrupted_image` - Corrupted file for error handling
- `mock_embedding` - Numpy array embedding (512-dim)
- `multiple_images` - List of images with different colors

## Test Dependencies

### Required
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `numpy` - Array operations
- `Pillow` - Image processing

### Optional (for full functionality)
- `transformers` - CLIP model (skipped tests if not available)
- `torch` - PyTorch backend
- `faiss-cpu` - Vector search (falls back to NumPy)
- `opencv-python` - Video processing
- `pytesseract` - OCR support

## Test Configuration

Tests are designed to:
- ✅ Run without external dependencies (graceful fallbacks)
- ✅ Clean up temporary files automatically
- ✅ Support parallel execution
- ✅ Provide clear failure messages
- ✅ Mock external services where appropriate
- ✅ Test both success and failure paths
- ✅ Verify performance characteristics
- ✅ Ensure thread safety

## Performance Benchmarks

Expected performance on standard hardware:

- **Image embedding**: < 1 second per image (SimpleEmbedder)
- **Text embedding**: < 0.1 seconds per query
- **Similarity search**: < 0.1 seconds for 10K items
- **Storage operation**: < 2 seconds per image
- **Concurrent operations**: Linear scaling up to 4 threads

## Continuous Integration

These tests are designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run multimodal memory tests
  run: |
    pytest tests/memory/ \
      --cov=dominusprime.agents.memory \
      --cov-report=xml \
      --junitxml=test-results.xml \
      -v
```

## Known Limitations

1. **CLIP Tests Skipped**: Tests requiring CLIP model are marked with `@pytest.mark.skipif` and run only when dependencies are available.

2. **Video Processing**: Video tests use minimal MP4 files; real video processing depends on `opencv-python`.

3. **OCR Tests**: OCR functionality requires `pytesseract` and is optional.

4. **Performance Tests**: Performance benchmarks may vary based on hardware and system load.

## Troubleshooting

### Tests Fail to Collect
- Ensure `tests/memory/__init__.py` exists
- Check Python import paths
- Verify all dependencies are installed

### Import Errors
```bash
# Install test dependencies
pip install -e ".[dev,multimodal]"
```

### Async Test Failures
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Fixture Not Found
- Check `conftest.py` is in the same directory
- Verify fixture names match usage
- Ensure pytest discovers conftest.py

## Contributing

When adding new tests:

1. **Follow naming convention**: `test_<functionality>.py`
2. **Group related tests**: Use test classes
3. **Add docstrings**: Explain what each test verifies
4. **Use fixtures**: Leverage shared fixtures
5. **Test edge cases**: Include error conditions
6. **Mock expensive operations**: Use mocks for external services
7. **Update this README**: Document new test coverage

## Test Quality Metrics

Current test suite quality:

- ✅ **Coverage**: Comprehensive unit and integration tests
- ✅ **Isolation**: Tests don't depend on each other
- ✅ **Speed**: Fast execution (< 2 minutes for full suite)
- ✅ **Reliability**: Deterministic, no flaky tests
- ✅ **Maintainability**: Clear structure and documentation
- ✅ **Completeness**: Tests success and failure paths
