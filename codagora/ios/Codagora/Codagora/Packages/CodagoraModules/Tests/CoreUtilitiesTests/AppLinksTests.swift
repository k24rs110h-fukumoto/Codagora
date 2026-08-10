//
//  AppLinksTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Testing
@testable import CoreUtilities

struct AppLinksTests {
    @Test("利用規約URLはHTTPSを使用する")
    func termsURLUsesHTTPS() {
        #expect(AppLinks.terms.scheme == "https")
    }

    @Test("利用規約URLにはホスト名が存在する")
    func termsURLHasHost() {
        #expect(AppLinks.terms.host != nil)
    }

    @Test("プライバシーポリシーURLはHTTPSを使用する")
    func privacyPolicyURLUsesHTTPS() {
        #expect(AppLinks.privacyPolicy.scheme == "https")
    }

    @Test("プライバシーポリシーURLにはホスト名が存在する")
    func privacyPolicyURLHasHost() {
        #expect(AppLinks.privacyPolicy.host != nil)
    }

    @Test("利用規約とプライバシーポリシーは異なるURLを使用する")
    func legalLinksAreDifferent() {
        #expect(
            AppLinks.terms != AppLinks.privacyPolicy
        )
    }
}
