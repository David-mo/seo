/*
 * inBeat — BlogPosting schema for the Blogs template (detail_blog, footer custom code)
 *
 * Replaces the block that currently reads:
 *     var dateModified = document.querySelector('#dateUpdated').innerHTML;
 * The template renders that element as id="updatedOn", so querySelector returns
 * null, .innerHTML throws, and the script aborts before injecting anything.
 * Verified: id="dateUpdated" appears in 0 of 264 crawled post pages.
 *
 * Changes vs the current script
 *   1. Reads #updatedOn, the id the template actually renders.
 *   2. Emits ISO 8601 dates. The DOM holds "March 19, 2026", which is not a
 *      valid datePublished value even once the selector is fixed.
 *   3. Emits a Person author on a normalised /author/{slug} URL. Bylines
 *      currently point at /author/x (83 posts), /blog/author/x (147, all 301)
 *      and "#" (34); the old script passed those through verbatim.
 *   4. References the Organization by @id instead of re-declaring it, so the
 *      stale uploads-ssl.webflow.com logo URL is no longer emitted.
 *   5. Removes the site-wide fallback node, which otherwise ships a second
 *      BlogPosting crediting the Organization with no dates. That fallback is
 *      an immediate IIFE, so it always runs before this DOMContentLoaded
 *      handler and its node is present by the time we get here.
 *   6. Guards every selector. The old script threw on the first missing element.
 */
(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  function text(selector) {
    var el = document.querySelector(selector);
    return el ? el.textContent.trim() : '';
  }

  function metaContent(selector) {
    var el = document.querySelector(selector);
    return el ? el.getAttribute('content') || '' : '';
  }

  // "March 19, 2026" -> "2026-03-19". Returns '' when unparseable so we omit
  // the property rather than publish a malformed date.
  function toISODate(raw) {
    if (!raw) return '';
    var d = new Date(raw);
    if (isNaN(d.getTime())) return '';
    return (
      d.getFullYear() +
      '-' +
      String(d.getMonth() + 1).padStart(2, '0') +
      '-' +
      String(d.getDate()).padStart(2, '0')
    );
  }

  // Collapse the real byline shapes onto the canonical /author/{slug}:
  //   /author/sehar-fatima       -> /author/sehar-fatima   (already correct)
  //   /blog/author/sehar-fatima  -> /author/sehar-fatima   (drops the 301 hop)
  //
  // Deliberately returns '' for href="#" (34 posts). Slugifying the displayed
  // name there invents URLs that 404 — "Luz Marina Dugarte Pulpeiro" would
  // yield /author/luz-marina-dugarte-pulpeiro when the CMS slug is "luz".
  // Those posts get a Person with a name and no url until the Designer rebind
  // in phase 2 gives them a real href.
  function authorUrlFrom(href) {
    if (!href || href === '#') return '';
    var path = href.split('?')[0].split('#')[0].replace(/\/+$/, '');
    var parts = path.split('/');
    var slug = parts[parts.length - 1] || '';
    return slug ? window.location.origin + '/author/' + slug : '';
  }

  ready(function () {
    var canonicalEl = document.querySelector('link[rel="canonical"]');
    var url = canonicalEl
      ? canonicalEl.href
      : window.location.origin + window.location.pathname;

    var authorEl = document.querySelector('#authorName');
    var authorName = authorEl ? authorEl.textContent.trim() : '';
    var authorUrl = authorEl ? authorUrlFrom(authorEl.getAttribute('href')) : '';

    var published = toISODate(text('#datePublished'));
    var modified = toISODate(text('#updatedOn')) || published;

    var headline =
      text('h1') || metaContent('meta[property="og:title"]') || document.title;

    var schema = {
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      '@id': url + '#blogposting',
      url: url,
      mainEntityOfPage: { '@type': 'WebPage', '@id': url },
      headline: headline.slice(0, 110),
      description: metaContent('meta[name="description"]'),
      isPartOf: { '@type': 'Blog', '@id': window.location.origin + '/blog#blog' },
      publisher: {
        '@type': 'Organization',
        '@id': window.location.origin + '/#organization'
      }
    };

    var image = metaContent('meta[property="og:image"]');
    if (image) schema.image = [image];
    if (published) schema.datePublished = published;
    if (modified) schema.dateModified = modified;

    if (authorName) {
      schema.author = authorUrl
        ? {
            '@type': 'Person',
            '@id': authorUrl + '#person',
            name: authorName,
            url: authorUrl
          }
        : { '@type': 'Person', name: authorName };
    }

    // Drop the site-wide fallback's Organization-authored node before adding ours.
    var stale = document.getElementById('global-blogposting-schema');
    if (stale && stale.parentNode) stale.parentNode.removeChild(stale);

    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'inbeat-blogposting-schema';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
  });
})();
