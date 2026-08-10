//
//  LoginView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/30.
//

import SwiftUI
import FeatureAuth
import CoreUtilities

struct LoginView: View {
    @StateObject private var viewModel: LoginViewModel
    @State private var isPasswordVisible: Bool = false
    
    let onLoginSuccess: (AuthenticatedUser) -> Void
    
    init(viewModel: LoginViewModel, onLoginSuccess: @escaping (AuthenticatedUser) -> Void) {
        _viewModel = StateObject(wrappedValue: viewModel)
        self.onLoginSuccess = onLoginSuccess
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color("CodagoraBackground")
                    .ignoresSafeArea()
                ScrollView {
                    VStack (spacing: 24){
                        
                        Spacer()
                        
                        VStack(spacing: 8) {
                            Image("AppLogo")
                                .resizable()
                                .scaledToFit()
                                .containerRelativeFrame(.horizontal) { width, _ in
                                    width * 0.16
                                }
                            
                            Image("AppTitle")
                                .resizable()
                                .renderingMode(.template)
                                .scaledToFit()
                                .foregroundStyle(Color("CodagoraNavy"))
                                .containerRelativeFrame(.horizontal) { width, _ in
                                    width * 0.8
                                }
                            
                            Text("集い、語り、つくる開発空間")
                                .font(.subheadline)
                                .foregroundStyle(Color("CodagoraSecondaryText"))
                        }
                        .frame(maxWidth: .infinity)
                        
                        VStack(spacing: 6) {
                            Text("メールアドレス")
                                .font(.subheadline)
                                .fontWeight(.semibold)
                                .foregroundStyle(Color("CodagoraNavy"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            
                            TextField("mail@example.com", text: $viewModel.email)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.emailAddress)
                                .textContentType(.emailAddress)
                                .textFieldStyle(.plain)
                                .foregroundStyle(Color("CodagoraNavy"))
                                .padding(.horizontal, 10)
                                .frame(height: 40)
                                .background {
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(Color("CodagoraFieldBackground"))
                                }
                                .overlay {
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color("CodagoraBorder"))
                                }
                        }
                        
                        VStack(spacing: 6) {
                            Text("パスワード")
                                .font(.subheadline)
                                .fontWeight(.semibold)
                                .foregroundStyle(Color("CodagoraNavy"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            
                            HStack(spacing: 8) {
                                if isPasswordVisible {
                                    TextField("", text: $viewModel.password)
                                        .textContentType(.password)
                                } else {
                                    SecureField("", text: $viewModel.password)
                                        .textContentType(.password)
                                }
                                
                                Button {
                                    isPasswordVisible.toggle()
                                } label: {
                                    Image(systemName: isPasswordVisible ? "eye.slash" : "eye")
                                        .foregroundStyle(Color("CodagoraSecondaryText"))
                                }
                                .buttonStyle(.plain)
                            }
                            .textFieldStyle(.plain)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .padding(.horizontal, 10)
                            .frame(height: 40)
                            .background {
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(Color("CodagoraFieldBackground"))
                            }
                            .overlay {
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color("CodagoraBorder"))
                            }
                            
                            if let errorMessage = viewModel.errorMessage {
                                Text(errorMessage)
                                    .font(.caption)
                                    .foregroundStyle(
                                        Color("CodagoraError")
                                    )
                                    .frame(
                                        maxWidth: .infinity,
                                        alignment: .leading
                                    )
                            }
                        }
                        
                        HStack {
                            NavigationLink {
                                ForgotPasswordView { email in
                                    print("再設定メール送信先: \(email)")
                                }
                            } label: {
                                Text("パスワードを忘れた方")
                                    .font(.subheadline)
                            }
                            
                            Text(" / ")
                                .font(.subheadline)
                                .foregroundStyle(Color("CodagoraSecondaryText"))
                            
                            NavigationLink {
                                LoginHelpView()
                            } label: {
                                Text("ログインでお困りの方")
                                    .font(.subheadline)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        
                        Button {
                            Task {
                                guard let user = await viewModel.login() else {
                                    return
                                }
                                onLoginSuccess(user)
                                viewModel.email = ""
                                viewModel.password = ""
                            }
                        } label: {
                            Group {
                                if viewModel.isLoading {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text("ログイン")
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!viewModel.canSubmit)
                        
                        Text(
                            "続行することで Codagora の[利用規約](\(AppLinks.terms.absoluteString))に同意し、[プライバシーポリシー](\(AppLinks.privacyPolicy.absoluteString))を確認したものとみなされます。"
                        )
                        .font(.footnote)
                        .multilineTextAlignment(.center)
                        .foregroundStyle(Color("CodagoraSecondaryText"))
                        
                        HStack {
                            Text("アカウントが未登録ですか？")
                                .font(.subheadline)
                                .foregroundStyle(Color("CodagoraSecondaryText"))
                            
                            NavigationLink {
                                RegisterView{
                                    print("")
                                }
                            } label: {
                                Text("新規アカウント登録")
                            }
                        }
                        Spacer()
                    }
                }
                .padding(24)
            }
        }
        .tint(Color("CodagoraBlue"))
    }
}

