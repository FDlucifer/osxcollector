#!/usr/bin/env python

# -*- coding: utf-8 -*-
#
# LookupDomainsFilter uses OpenDNS to lookup the values in 'osxcollector_domains' and add 'osxcollector_opendns' key.
#
from osxcollector.output_filters.base_filters.output_filter import run_filter
from osxcollector.output_filters.base_filters. \
    threat_feed import ThreatFeedFilter
from osxcollector.output_filters.opendns.api import InvestigateApi


class LookupDomainsFilter(ThreatFeedFilter):

    """Uses OpenDNS to lookup the values in 'osxcollector_domains' and add 'osxcollector_opendns' key."""

    def __init__(self, only_lookup_when=None, is_suspicious_when=None):
        super(LookupDomainsFilter, self).__init__('osxcollector_domains', 'osxcollector_opendns',
                                                  only_lookup_when=only_lookup_when, is_suspicious_when=is_suspicious_when,
                                                  api_key='opendns')

    def _lookup_iocs(self):
        """Caches the OpenDNS info for a set of domains"""
        investigate = InvestigateApi(self._api_key)

        categorized_responses = investigate.categorization(list(self._all_iocs))
        for domain in categorized_responses.keys():
            if not self._should_get_security_info(domain, categorized_responses[domain]):
                del categorized_responses[domain]

        security_responses = investigate.security(categorized_responses.keys())
        for domain in security_responses.keys():
            if self._should_store_ioc_info(categorized_responses[domain], security_responses[domain]):
                self._threat_info_by_iocs[domain] = {
                    'domain': domain,
                    'categorization': categorized_responses[domain],
                    'security': security_responses[domain],
                    'link': 'https://investigate.opendns.com/domain-view/name/{0}/view'.format(domain)
                }

    def _should_get_security_info(self, domain, categorized_info):
        """Figure out whether the info on the domain is interesting enough to gather more data."""
        if categorized_info['is_suspicious']:
            return True
        if (0 == categorized_info['status'] and
                0 == len(categorized_info.get('content_categories', [])) and
                0 == len(categorized_info.get('security_categories', []))):
            return True
        if domain in self._suspicious_iocs:
            return True
        return False

    def _should_store_ioc_info(self, categorized_info, security):
        """Figure out whether the data gathered is interesting enough to store in the output."""
        return categorized_info['is_suspicious'] or security['is_suspicious']


def main():
    run_filter(LookupDomainsFilter())


if __name__ == "__main__":
    main()
