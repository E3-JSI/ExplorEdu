//
//  ViewController.m
//  ExplorEdu
//
//  Created by Jan Berčič on 19/11/15.
//  Copyright (c) 2015 IJS. All rights reserved.
//

#import "MainWebViewController.h"

@interface MainWebViewController ()

@end

@implementation MainWebViewController

- (void)viewDidLoad
{
	[super viewDidLoad];
	[self.mainBrowser loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:@"http://exploredu.ijs.si:8888/"]]];
}

- (void)didReceiveMemoryWarning
{
	[super didReceiveMemoryWarning];
	// Dispose of any resources that can be recreated.
}

#pragma mark - Web View Delegate

- (void)webViewDidFinishLoad:(UIWebView*)webView
{
	NSLog(@"webview finished loading with no error");
}

- (void)webView:(UIWebView*)webView didFailLoadWithError:(NSError*)error
{
	NSLog(@"webview failed with error: %@",error);
}

- (BOOL)webView:(UIWebView*)webView shouldStartLoadWithRequest:(NSURLRequest*)request navigationType:(UIWebViewNavigationType)navigationType
{
	if (![request.URL.host isEqualToString:@"exploredu.ijs.si"])
	{
		[[UIApplication sharedApplication] openURL:request.URL];
		return NO;
	}
	return YES;
}

@end
