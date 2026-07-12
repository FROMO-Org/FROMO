import 'package:dio/dio.dart';
import 'package:fromo/core/api_client.dart';

class FakeApiClient extends ApiClient {
  FakeApiClient({
    this.onGet,
    this.onPost,
    this.onPatch,
    this.onDelete,
  });

  final Future<Response<dynamic>> Function(String path, Map<String, dynamic>? params)?
      onGet;
  final Future<Response<dynamic>> Function(String path, dynamic data)? onPost;
  final Future<Response<dynamic>> Function(String path, dynamic data)? onPatch;
  final Future<Response<dynamic>> Function(String path)? onDelete;

  @override
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? params}) async {
    final response = await onGet!(path, params);
    return Response<T>(
      data: response.data as T,
      requestOptions: response.requestOptions,
      statusCode: response.statusCode,
    );
  }

  @override
  Future<Response<T>> post<T>(String path, {data}) async {
    final response = await onPost!(path, data);
    return Response<T>(
      data: response.data as T,
      requestOptions: response.requestOptions,
      statusCode: response.statusCode,
    );
  }

  @override
  Future<Response<T>> patch<T>(String path, {data}) async {
    final response = await onPatch!(path, data);
    return Response<T>(
      data: response.data as T,
      requestOptions: response.requestOptions,
      statusCode: response.statusCode,
    );
  }

  @override
  Future<Response<T>> delete<T>(String path) async {
    final response = await onDelete!(path);
    return Response<T>(
      data: response.data as T,
      requestOptions: response.requestOptions,
      statusCode: response.statusCode,
    );
  }
}
