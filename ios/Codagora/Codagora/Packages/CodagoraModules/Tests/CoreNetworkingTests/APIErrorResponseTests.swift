//
//  APIErrorResponseTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation
import Testing
@testable import CoreNetworking

struct APIErrorResponseTests {
    @Test("detail形式のエラーメッセージを取得する")
    func decodesDetailMessage() throws {
        let data = Data(
            #"{"detail":"認証情報が含まれていません。"}"#.utf8
        )

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(
            response.primaryMessage ==
            "認証情報が含まれていません。"
        )
    }

    @Test("message形式のエラーメッセージを取得する")
    func decodesMessage() throws {
        let data = Data(
            #"{"message":"ログインに失敗しました。"}"#.utf8
        )

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(
            response.primaryMessage ==
            "ログインに失敗しました。"
        )
    }

    @Test("項目別エラーから最初のメッセージを取得する")
    func decodesFieldErrors() throws {
        let data = Data(
            """
            {
              "errors": {
                "password": [
                  "パスワードが短すぎます。"
                ],
                "email": [
                  "このメールアドレスは使用されています。"
                ]
              }
            }
            """.utf8
        )

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(
            response.primaryMessage ==
            "このメールアドレスは使用されています。"
        )
    }

    @Test("detailをmessageより優先する")
    func prioritizesDetailOverMessage() throws {
        let data = Data(
            """
            {
              "detail": "detailのエラー",
              "message": "messageのエラー",
              "errors": {
                "email": [
                  "項目別エラー"
                ]
              }
            }
            """.utf8
        )

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(
            response.primaryMessage ==
            "detailのエラー"
        )
    }

    @Test("detailが空の場合はmessageを使用する")
    func fallsBackToMessage() throws {
        let data = Data(
            """
            {
              "detail": "",
              "message": "代わりのメッセージ"
            }
            """.utf8
        )

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(
            response.primaryMessage ==
            "代わりのメッセージ"
        )
    }

    @Test("メッセージが存在しない場合はnilを返す")
    func returnsNilWithoutMessages() throws {
        let data = Data(#"{}"#.utf8)

        let response = try JSONDecoder().decode(
            APIErrorResponse.self,
            from: data
        )

        #expect(response.primaryMessage == nil)
    }
}
