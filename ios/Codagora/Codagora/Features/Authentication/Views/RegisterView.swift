//
//  RegisterView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/31.
//

import SwiftUI
import CoreUtilities

struct RegisterView: View {
    @State private var firstName: String = ""
    @State private var lastName: String = ""
    @State private var email: String = ""
    @State private var userName: String = ""
    @State private var password: String = ""
    @State private var confirmPassword: String = ""
    @State private var acceptsTerms: Bool = false
    @State private var isPasswordVisible: Bool = false
    @State private var isConfirmPasswordVisible: Bool = false
    
    let onRegisterSuccess: () -> Void
    
    private var isFormValid: Bool {
        ValidationUtility.isValidName(firstName) &&
        ValidationUtility.isValidName(lastName) &&
        ValidationUtility.isValidUsername(userName) &&
        ValidationUtility.isValidEmail(email) &&
        ValidationUtility.isValidPassword(password) &&
        ValidationUtility.passwordsMatch(password, confirmPassword) &&
        acceptsTerms
    }
    
    var body: some View {
        ZStack {
            Color("CodagoraBackground")
                .ignoresSafeArea()
            ScrollView {
                VStack(spacing: 24) {
                    VStack {
                        Image("AppTitle")
                            .resizable()
                            .renderingMode(.template)
                            .scaledToFit()
                            .foregroundStyle(Color("CodagoraNavy"))
                            .containerRelativeFrame(.horizontal) { width, _ in
                                width * 0.8
                            }
                        
                        Text("アカウント登録")
                            .font(.title3)
                            .foregroundStyle(Color("CodagoraSecondaryText"))
                    }
                    .frame(maxWidth: .infinity)
                    // 氏名入力欄
                    VStack {
                        Text("氏名")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                        HStack {
                            VStack {
                                TextField("姓*", text: $lastName)
                                    .textContentType(.familyName)
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
                                
                                if !lastName.isEmpty && !ValidationUtility.isValidName(lastName) {
                                    Text("入力必須欄")
                                        .font(.caption)
                                        .foregroundStyle(Color("CodagoraError"))
                                }
                            }
                            
                            VStack {
                                TextField("名*", text: $firstName)
                                    .textContentType(.givenName)
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
                                
                                if !firstName.isEmpty && !ValidationUtility.isValidName(firstName) {
                                    Text("入力必須欄")
                                        .font(.caption)
                                        .foregroundStyle(Color("CodagoraError"))
                                }
                            }
                        }
                    }
                    
                    // ユーザー名入力欄
                    VStack(spacing: 6) {
                        Text("ユーザー名")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                        
                        TextField("ユーザー名*", text: $userName)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.asciiCapable)
                            .textContentType(.username)
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
                        
                        if !userName.isEmpty && !ValidationUtility.isValidUsername(userName) {
                            Text("条件に合うなユーザー名ではありません")
                                .font(.caption)
                                .foregroundStyle(Color("CodagoraError"))
                        }
                        
                        
                        VStack(spacing: 8) {
                            HStack(alignment: .top) {
                                Text("・")
                                    .fontWeight(.bold)
                                Text("半角英数字と-（ハイフン）が使用可能")
                            }
                            .font(.footnote)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            
                            HStack(alignment: .top) {
                                Text("・")
                                    .fontWeight(.bold)
                                Text("30文字以内")
                            }
                            .font(.footnote)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    
                    // メールアドレス入力欄
                    VStack(spacing: 6) {
                        Text("メールアドレス")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                        
                        TextField("mail@example.com", text: $email)
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
                        
                        if !email.isEmpty && !ValidationUtility.isValidEmail(email) {
                            Text("有効なメールアドレスではありません")
                                .font(.caption)
                                .foregroundStyle(Color("CodagoraError"))
                        }
                    }
                    
                    // パスワード入力欄
                    VStack(spacing: 6) {
                        Text("パスワード")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(Color("CodagoraNavy"))
                            .frame(maxWidth: .infinity, alignment: .leading)
                        
                        HStack(spacing: 8) {
                            if isPasswordVisible {
                                TextField("パスワード*", text: $password)
                                    .textContentType(.newPassword)
                            } else {
                                SecureField("パスワード*", text: $password)
                                    .textContentType(.newPassword)
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
                        
                        VStack(spacing: 8) {
                            if ValidationUtility.containsUppercase(password) &&
                                ValidationUtility.containsLowercase(password) &&
                                ValidationUtility.containsNumber(password) {
                                HStack(alignment: .top) {
                                    Text("・")
                                        .fontWeight(.bold)
                                    Text("半角英字の大文字と小文字、さらに半角数字を一つ含める")
                                }
                                .font(.footnote)
                                .foregroundStyle(Color("CodagoraSuccess"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            } else {
                                HStack(alignment: .top) {
                                    Text("・")
                                        .fontWeight(.bold)
                                    Text("半角英字の大文字と小文字、さらに半角数字を一つ含める")
                                }
                                .font(.footnote)
                                .foregroundStyle(Color("CodagoraError"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            
                            if ValidationUtility.hasValidPasswordLength(password){
                                HStack(alignment: .top) {
                                    Text("・")
                                        .fontWeight(.bold)
                                    Text("8文字以上")
                                }
                                .font(.footnote)
                                .foregroundStyle(Color("CodagoraSuccess"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            } else {
                                HStack(alignment: .top) {
                                    Text("・")
                                        .fontWeight(.bold)
                                    Text("8文字以上")
                                }
                                .font(.footnote)
                                .foregroundStyle(Color("CodagoraError"))
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            
                            HStack(spacing: 8) {
                                if isConfirmPasswordVisible {
                                    TextField("パスワード再度入力*", text: $confirmPassword)
                                        .textContentType(.newPassword)
                                } else {
                                    SecureField("パスワード再度入力*", text: $confirmPassword)
                                        .textContentType(.newPassword)
                                }
                                
                                Button {
                                    isConfirmPasswordVisible.toggle()
                                } label: {
                                    Image(systemName: isConfirmPasswordVisible ? "eye.slash" : "eye")
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
                            
                            if !confirmPassword.isEmpty && !ValidationUtility.passwordsMatch(password, confirmPassword) {
                                Text("パスワードが一致しません")
                                    .font(.caption)
                                    .foregroundStyle(Color("CodagoraError"))
                            }
                        }
                        
                        Toggle(
                                """
                                [利用規約](\(AppLinks.terms.absoluteString))と\
                                [プライバシーポリシー](\(AppLinks.privacyPolicy.absoluteString))\
                                に同意します
                                """,
                                isOn: $acceptsTerms
                        )
                        .font(.footnote)
                        
                        Button {
                            onRegisterSuccess()
                        } label: {
                            Text("アカウントを作成")
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!isFormValid)
                    }
                    
                }
                .padding(24)
            }
        }
        .tint(Color("CodagoraBlue"))
        .navigationTitle("新規登録")
        .navigationBarTitleDisplayMode(.inline)
    }
}
