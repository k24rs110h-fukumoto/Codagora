//
//  ForgotPasswordView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/31.
//

import SwiftUI
import CoreUtilities

struct ForgotPasswordView: View {
    @State private var email: String = ""
    @State private var isSubmitted: Bool = false
    
    @Environment(\.dismiss) private var dismiss
    
    let onSendResetLink: (String) -> Void
    
    var body: some View {
        ZStack {
            Color("CodagoraBackground")
                .ignoresSafeArea()
            
            ScrollView {
                if isSubmitted {
                    submittedContent
                } else {
                    formContent
                }
            }
        }
        .tint(Color("CodagoraBlue"))
        .navigationTitle("パスワード再設定")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private var formContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: "lock.rotation")
                    .font(.system(size: 48))
                    .foregroundStyle(Color("CodagoraNavy"))
                
                Text("パスワードをお忘れですか？")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(Color("CodagoraNavy"))
                
                Text(
                    "登録したメールアドレスを入力してください。パスワード再設定用の案内を送信します。"
                )
                .font(.subheadline)
                .foregroundStyle(Color("CodagoraSecondaryText"))
            }
            
            VStack(alignment: .leading, spacing: 6) {
                Text("メールアドレス")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(Color("CodagoraNavy"))
                
                TextField("mail@example.com", text: $email)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    .submitLabel(.send)
                    .textFieldStyle(.plain)
                    .foregroundStyle(Color("CodagoraNavy"))
                    .padding(.horizontal, 10)
                    .frame(height: 46)
                    .background {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color("CodagoraFieldBackground"))
                    }
                    .overlay {
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color("CodagoraBorder"))
                    }
                    .onSubmit {
                        sendResetLink()
                    }
                
                if !email.isEmpty && !ValidationUtility.isValidEmail(email) {
                    Text("有効なメールアドレスを入力してください")
                        .font(.caption)
                        .foregroundStyle(Color("CodagoraError"))
                }
            }
            
            Button {
                sendResetLink()
            } label: {
                Text("再設定メールを送信")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
            .disabled(!ValidationUtility.isValidEmail(email))
        }
        .padding(24)
    }
    
    private var submittedContent: some View {
        VStack(spacing: 24) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundStyle(Color("CodagoraBlue"))
            
            VStack(spacing: 8) {
                Text("メールをご確認ください")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(Color("CodagoraNavy"))
                
                Text(
                    "入力されたメールアドレスが登録されている場合、パスワード再設定用の案内を送信しました。"
                )
                .font(.subheadline)
                .foregroundStyle(Color("CodagoraSecondaryText"))
                .multilineTextAlignment(.center)
            }
            
            Button {
                dismiss()
            } label: {
                Text("ログイン画面に戻る")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
    }
    
    private func sendResetLink() {
        guard ValidationUtility.isValidEmail(email) else {
            return
        }
        
        onSendResetLink(email)
        isSubmitted = true
    }
}
