//
//  LoginHelpView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/31.
//

import SwiftUI
import CoreUtilities

struct LoginHelpView: View {
    var body: some View {
        ZStack {
            Color("CodagoraBackground")
                .ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 12) {
                        Image(systemName: "questionmark.circle.fill")
                            .font(.system(size: 48))
                            .symbolRenderingMode(.hierarchical)
                            .foregroundStyle(Color("CodagoraBlue"))

                        Text("ログインでお困りですか？")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundStyle(Color("CodagoraNavy"))

                        Text(
                            "ログインできない場合は、以下の項目をご確認ください。"
                        )
                        .font(.subheadline)
                        .foregroundStyle(Color("CodagoraSecondaryText"))
                    }

                    VStack(spacing: 0) {
                        DisclosureGroup {
                            Text(
                                "登録時に使用したメールアドレスを入力してください。前後に空白が入っていないか、入力内容に誤りがないか確認してください。"
                            )
                            .font(.subheadline)
                            .foregroundStyle(
                                Color("CodagoraSecondaryText")
                            )
                            .padding(.top, 12)
                        } label: {
                            Label(
                                "メールアドレスを確認する",
                                systemImage: "envelope"
                            )
                            .foregroundStyle(Color("CodagoraNavy"))
                        }
                        .padding()

                        Divider()

                        DisclosureGroup {
                            Text(
                                "英字の大文字・小文字や数字に誤りがないか、余分な空白が入力されていないか確認してください。"
                            )
                            .font(.subheadline)
                            .foregroundStyle(
                                Color("CodagoraSecondaryText")
                            )
                            .padding(.top, 12)
                        } label: {
                            Label(
                                "パスワードを確認する",
                                systemImage: "lock"
                            )
                            .foregroundStyle(Color("CodagoraNavy"))
                        }
                        .padding()

                        Divider()

                        DisclosureGroup {
                            Text(
                                "Wi-Fiまたはモバイル通信に接続されているか確認してください。通信状態が不安定な場合は、時間を置いて再度お試しください。"
                            )
                            .font(.subheadline)
                            .foregroundStyle(
                                Color("CodagoraSecondaryText")
                            )
                            .padding(.top, 12)
                        } label: {
                            Label(
                                "通信環境を確認する",
                                systemImage: "wifi"
                            )
                            .foregroundStyle(Color("CodagoraNavy"))
                        }
                        .padding()
                    }
                    .background {
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color("CodagoraFieldBackground"))
                    }
                    .overlay {
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color("CodagoraBorder"))
                    }

                    NavigationLink {
                        ForgotPasswordView { email in
                            print("再設定メール送信先: \(email)")
                        }
                    } label: {
                        Label(
                            "パスワードを再設定する",
                            systemImage: "key"
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent)

                    VStack(alignment: .leading, spacing: 8) {
                        Text(
                            "上記を確認してもログインできない場合は、お問い合わせください。"
                        )
                        .font(.footnote)
                        .foregroundStyle(Color("CodagoraSecondaryText"))

                        Link(
                            "お問い合わせ",
                            destination: AppLinks.contact
                        )
                        .font(.subheadline)
                    }
                }
                .padding(24)
            }
        }
        .tint(Color("CodagoraBlue"))
        .navigationTitle("ログインヘルプ")
        .navigationBarTitleDisplayMode(.inline)
    }
}
