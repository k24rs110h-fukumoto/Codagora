//
//  AuthErrorMapper.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation
import CoreNetworking

public enum AuthErrorMapper {
    public static func message(
        for error: Error
    ) -> String {
        guard let networkError = error as? NetworkError else {
            return "予期しないエラーが発生しました。"
        }

        switch networkError {
        case .invalidURL,
             .invalidResponse,
             .requestEncodingFailed,
             .responseDecodingFailed:
            return "通信処理で問題が発生しました。"

        case let .badRequest(response):
            return response?.primaryMessage
                ?? "入力内容を確認してください。"

        case .unauthorized:
            return "メールアドレスまたはパスワードが正しくありません。"

        case .forbidden:
            return "この操作を実行する権限がありません。"

        case .notFound:
            return "対象の情報が見つかりませんでした。"

        case let .conflict(response):
            return response?.primaryMessage
                ?? "入力された情報はすでに使用されています。"

        case .tooManyRequests:
            return "操作回数が多すぎます。しばらく待ってから再度お試しください。"

        case .serverError:
            return "サーバーで問題が発生しました。しばらく待ってから再度お試しください。"

        case .unexpectedStatusCode:
            return "予期しない通信エラーが発生しました。"

        case let .transport(code):
            return transportMessage(for: code)
        }
    }

    private static func transportMessage(
        for code: URLError.Code
    ) -> String {
        switch code {
        case .notConnectedToInternet:
            return "インターネット接続を確認してください。"

        case .timedOut:
            return "通信がタイムアウトしました。再度お試しください。"

        case .networkConnectionLost:
            return "通信が途中で切断されました。"

        case .cannotFindHost,
             .cannotConnectToHost,
             .dnsLookupFailed:
            return "サーバーへ接続できませんでした。"

        default:
            return "通信に失敗しました。再度お試しください。"
        }
    }
}
