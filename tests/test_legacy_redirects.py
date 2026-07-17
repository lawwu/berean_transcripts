from berean_transcripts.legacy_redirects import write_legacy_redirects


def test_write_legacy_redirects_preserves_both_old_url_shapes(tmp_path):
    sermons = tmp_path / "sermons"
    sermons.mkdir()
    (sermons / "video-id.html").write_text("new page", encoding="utf-8")

    count = write_legacy_redirects(tmp_path, "https://example.com/archive")

    assert count == 3
    root_redirect = (tmp_path / "video-id.html").read_text(encoding="utf-8")
    transcript_redirect = (tmp_path / "transcript_video-id.html").read_text(
        encoding="utf-8"
    )
    assert 'url=sermons/video-id.html' in root_redirect
    assert (
        'href="https://example.com/archive/sermons/video-id.html"'
        in root_redirect
    )
    assert transcript_redirect == root_redirect
    assert 'url=index.html#archive' in (
        tmp_path / "legacy_index.html"
    ).read_text(encoding="utf-8")
